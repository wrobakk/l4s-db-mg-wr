#include "ns3/command-line.h"
#include "ns3/config.h"
#include "ns3/uinteger.h"
#include "ns3/boolean.h"
#include "ns3/double.h"
#include "ns3/string.h"
#include "ns3/log.h"
#include "ns3/yans-wifi-helper.h"
#include "ns3/ssid.h"
#include "ns3/mobility-helper.h"
#include "ns3/internet-stack-helper.h"
#include "ns3/ipv4-address-helper.h"
#include "ns3/udp-client-server-helper.h"
#include "ns3/packet-sink-helper.h"
#include "ns3/on-off-helper.h"
#include "ns3/ipv4-global-routing-helper.h"
#include "ns3/packet-sink.h"
#include "ns3/yans-wifi-channel.h"
#include <chrono> // For high resolution clock
#include "ns3/wifi-net-device.h"
#include "ns3/qos-txop.h"
#include "ns3/wifi-mac.h"
#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/wifi-module.h"
#include "ns3/txop.h"
#include <fstream>
#include <sstream>
#include <map>
#include "ns3/arp-cache.h"
#include "ns3/ipv4-l3-protocol.h"
#include "ns3/arp-l3-protocol.h"
#include "ns3/node-list.h"
#include "ns3/ipv4-interface.h"
#include "ns3/ipv4-header.h"
#include "ns3/packet.h"
#include "ns3/pointer.h"
#include <memory>
#include <algorithm>

using namespace ns3;

static uint32_t trace_nDbWifi = 0;  //tracing values for txop file
static uint32_t trace_nEbWifi = 0;
static bool trace_enableRts = false;

void PopulateARPcache () 
{
    Ptr<ArpCache> arp = CreateObject<ArpCache> ();
    arp->SetAliveTimeout (Seconds (3600 * 24 * 365) );

    for (NodeList::Iterator i = NodeList::Begin (); i != NodeList::End (); ++i)
    {
        Ptr<Ipv4L3Protocol> ip = (*i)->GetObject<Ipv4L3Protocol> ();
        NS_ASSERT(ip != Ptr<Ipv4L3Protocol>());
        ObjectVectorValue interfaces;
        ip->GetAttribute ("InterfaceList", interfaces);

        for (ObjectVectorValue::Iterator j = interfaces.Begin (); j != interfaces.End (); j++)
        {
            Ptr<Ipv4Interface> ipIface = (*j).second->GetObject<Ipv4Interface> ();
            NS_ASSERT(ipIface != Ptr<Ipv4Interface>());
            Ptr<NetDevice> device = ipIface->GetDevice ();
            NS_ASSERT(device != Ptr<NetDevice>());
            Mac48Address addr = Mac48Address::ConvertFrom (device->GetAddress () );

            for (uint32_t k = 0; k < ipIface->GetNAddresses (); k++)
            {
                Ipv4Address ipAddr = ipIface->GetAddress (k).GetLocal();
                if (ipAddr == Ipv4Address::GetLoopback ())
                    continue;

                ArpCache::Entry *entry = arp->Add (ipAddr);
                Ipv4Header ipv4Hdr;
                ipv4Hdr.SetDestination (ipAddr);
                Ptr<Packet> p = Create<Packet> (100);
                entry->MarkWaitReply (ArpCache::Ipv4PayloadHeaderPair (p, ipv4Hdr));
                entry->MarkAlive (addr);
            }
        }
    }

    for (NodeList::Iterator i = NodeList::Begin (); i != NodeList::End (); ++i)
    {
        Ptr<Ipv4L3Protocol> ip = (*i)->GetObject<Ipv4L3Protocol> ();
        NS_ASSERT(ip != Ptr<Ipv4L3Protocol>());
        ObjectVectorValue interfaces;
        ip->GetAttribute ("InterfaceList", interfaces);

        for (ObjectVectorValue::Iterator j = interfaces.Begin (); j != interfaces.End (); j ++)
        {
            Ptr<Ipv4Interface> ipIface = (*j).second->GetObject<Ipv4Interface> ();
            ipIface->SetAttribute ("ArpCache", PointerValue (arp) );
        }
    }
}

static std::string BuildTxopFilename(const std::string& prefix);
static void TxopTraceDb(uint32_t nodeId, Time start, Time duration, uint8_t linkId, bool failed);
static void TxopTraceEb(uint32_t nodeId, Time start, Time duration, uint8_t linkId, bool failed);
void LogIpt(uint32_t nodeId, uint8_t linkId, uint32_t ipt);
void LogInitialBackoff(uint32_t nodeId, uint8_t linkId, uint32_t backoff);
void LogDeterministicBackoff(uint32_t nodeId, uint8_t linkId, uint32_t backoff);
void LogIntermediateBackoff(uint32_t nodeId, uint8_t linkId,  uint32_t backoff);
void LogBackoff(uint32_t nodeId, uint8_t linkId,  uint32_t backoff);


int main(int argc, char *argv[])
{
    uint32_t nDbWifi = 1;
    uint32_t nEbWifi = 1;
    uint32_t mcs = 11;
    uint32_t channelWidth = 20;
    uint32_t gi = 800;
    bool enableRts = true;
    uint32_t payloadSize = 1450;
    uint32_t offeredRate = 150e6;
    bool pcap= false;

    double simulationTime = 30;
    double baseStart = 0;
    double gap = 1;
    double warmup = 30.0;

    // Parse command line arguments
    CommandLine cmd;
    cmd.AddValue("nDbWifi", "Number of DB stations", nDbWifi);
    cmd.AddValue("nEbWifi", "Number of EB stations", nEbWifi);
    cmd.AddValue("mcs", "HE MCS index", mcs);
    cmd.AddValue("channelWidth", "Channel width [MHz]", channelWidth);
    cmd.AddValue("gi", "Guard interval [ns]", gi);
    cmd.AddValue("enableRts", "Enable RTS/CTS", enableRts);
    cmd.AddValue("payloadSize", "UDP payload size [B]", payloadSize);
    cmd.AddValue("simulationTime", "Simulation time [s]", simulationTime);
    cmd.AddValue("baseStart", "Base start time [s]", baseStart);
    cmd.AddValue("gap", "Gap between starts [s]", gap);
    cmd.AddValue("warmup", "Warm-up after last start [s]", warmup);
    cmd.AddValue("pcap", "Generate a PCAP file from the AP", pcap);
    cmd.Parse(argc, argv);

    std::cout << "\n================ Simulation configuration ================\n";
    std::cout << "Stations: DB=" << nDbWifi << ", EB=" << nEbWifi<<"\n";
    std::cout << "PHY/MAC:  802.11ax, 5 GHz, channelWidth=" << channelWidth
              << " MHz, GI=" << gi << " ns, MCS=HeMcs" << mcs << "\n";
    std::cout << "RTS/CTS:  " << (enableRts ? "ENABLED" : "DISABLED") << "\n";
    std::cout << "Timing:   simulationTime=" << simulationTime << " s, baseStart=" << baseStart
              << " s, gap=" << gap << " s, warmup=" << warmup << " s\n";

    std::ofstream("deterministic-backoff-trace.csv", std::ios::out).close();
    std::ofstream("ipt-backoff-trace.csv", std::ios::out).close();  
    std::ofstream("backoff-trace.csv", std::ios::out).close();

    // RTS/CTS
    if (!enableRts)
    {
        Config::SetDefault("ns3::WifiRemoteStationManager::RtsCtsThreshold", StringValue("999999"));
    }
    else
    {
        Config::SetDefault("ns3::WifiRemoteStationManager::RtsCtsThreshold", StringValue("0"));
        Config::SetDefault("ns3::WifiDefaultProtectionManager::EnableMuRts", BooleanValue(true));
    }

    Config::SetDefault("ns3::WifiMacQueue::MaxDelay", TimeValue(Seconds(simulationTime)));

    trace_nDbWifi = nDbWifi;
    trace_nEbWifi = nEbWifi;
    trace_enableRts = enableRts;
    // Nodes
    NodeContainer staDbNodes, staEbNodes;
    staDbNodes.Create(nDbWifi);
    staEbNodes.Create(nEbWifi);

    NodeContainer apDbNode, apEbNode;
    apDbNode.Create(1);
    apEbNode.Create(1);

    // The same channel for both BSSs
    YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
    YansWifiPhyHelper phy;
    phy.SetChannel(channel.Create());

    std::string channelStr("{0, " + std::to_string(channelWidth) + ", BAND_5GHZ, 0}");
    phy.Set("ChannelSettings", StringValue(channelStr));

    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211ax);

    wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
                                     "DataMode",
                                     StringValue("HeMcs11"),
                                     "ControlMode",
                                     StringValue("OfdmRate24Mbps")); 

    WifiMacHelper mac;
    Ssid ssidDb = Ssid("BSS-DB");
    Ssid ssidEb = Ssid("BSS-EB");

    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssidDb));
    NetDeviceContainer staDbDevice = wifi.Install(phy, mac, staDbNodes);

    mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssidEb));
    NetDeviceContainer staEbDevice = wifi.Install(phy, mac, staEbNodes);

    // Mobility
    MobilityHelper mobility;
    mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");

    {
        Ptr<ListPositionAllocator> apPos = CreateObject<ListPositionAllocator>();
        apPos->Add(Vector(2.0, 2.0, 0.0));
        apPos->Add(Vector(2.0, 2.0, 0.0));
        mobility.SetPositionAllocator(apPos);
        mobility.Install(apDbNode);
        mobility.Install(apEbNode);
    }

    {
        Ptr<ListPositionAllocator> staDbPos = CreateObject<ListPositionAllocator>();
        for (uint32_t i = 0; i < nDbWifi; ++i)
        {
            staDbPos->Add(Vector(3.0, 2.0, 0.0));
        }
        mobility.SetPositionAllocator(staDbPos);
        mobility.Install(staDbNodes);
    }

    {
        Ptr<ListPositionAllocator> staEbPos = CreateObject<ListPositionAllocator>();
        for (uint32_t i = 0; i < nEbWifi; ++i)
        {
            staEbPos->Add(Vector(3.0, 2.0, 0.0));
        }
        mobility.SetPositionAllocator(staEbPos);
        mobility.Install(staEbNodes);
    }

    // AP DB with BeaconJitter
    mac.SetType("ns3::ApWifiMac",
                "Ssid", SsidValue(ssidDb),
                "EnableBeaconJitter", BooleanValue(true),
                "BeaconJitter", StringValue("ns3::UniformRandomVariable"));

    NetDeviceContainer apDbDevice = wifi.Install(phy, mac, apDbNode);  

    // AP EB with BeaconJitter
    mac.SetType("ns3::ApWifiMac",
                "Ssid", SsidValue(ssidEb),
                "EnableBeaconJitter", BooleanValue(true),
                "BeaconJitter", StringValue("ns3::UniformRandomVariable"));

    NetDeviceContainer apEbDevice = wifi.Install(phy, mac, apEbNode);

    Config::Set("/NodeList/*/DeviceList/*/$ns3::WifiNetDevice/HeConfiguration/GuardInterval",
                TimeValue(NanoSeconds(gi)));

    // Enable DB on DbSta
    for (uint32_t i = 0; i < staDbDevice.GetN(); ++i)
    {
        Ptr<WifiNetDevice> netDev = DynamicCast<WifiNetDevice>(staDbDevice.Get(i));
        Ptr<WifiMac> wifiMac = netDev->GetMac();
        Ptr<QosTxop> txop = wifiMac->GetQosTxop(AC_BE);
        if (txop)
        {
            txop->EnableDeterministicBackoff(true);
            txop->TraceConnectWithoutContext("TxopTrace",MakeBoundCallback(&TxopTraceDb, netDev->GetNode()->GetId()));

            txop->TraceConnectWithoutContext("IptTrace",
                MakeBoundCallback(&LogIpt, netDev->GetNode()->GetId()));
            // txop->TraceConnectWithoutContext("InitialBackoffTrace",
            //     MakeBoundCallback(&LogInitialBackoff, netDev->GetNode()->GetId()));
            txop->TraceConnectWithoutContext("DeterministicBackoffTrace",
                MakeBoundCallback(&LogDeterministicBackoff, netDev->GetNode()->GetId()));
        //     txop->TraceConnectWithoutContext("IntermediateBackoffTrace",
        //         MakeBoundCallback(&LogIntermediateBackoff, netDev->GetNode()->GetId()));
            txop->TraceConnectWithoutContext("BackoffTrace",
                MakeBoundCallback(&LogBackoff, netDev->GetNode()->GetId()));
        }
    }

    // EbSta
    for (uint32_t i = 0; i < staEbDevice.GetN(); ++i)
    {
        Ptr<WifiNetDevice> netDev = DynamicCast<WifiNetDevice>(staEbDevice.Get(i));
        Ptr<WifiMac> wifiMac = netDev->GetMac();
        Ptr<QosTxop> txop = wifiMac->GetQosTxop(AC_BE);
        if (txop)
        {
            txop->TraceConnectWithoutContext("TxopTrace",MakeBoundCallback(&TxopTraceEb, netDev->GetNode()->GetId()));
        }
    }

    // Internet stack
    InternetStackHelper stack;
    stack.Install(apDbNode);
    stack.Install(apEbNode);
    stack.Install(staDbNodes);
    stack.Install(staEbNodes);

    // IP addressing
    Ipv4AddressHelper address;

    address.SetBase("192.168.1.0", "255.255.255.0");
    Ipv4InterfaceContainer apDbInterface = address.Assign(apDbDevice);
    Ipv4InterfaceContainer staDbInterface = address.Assign(staDbDevice);

    address.SetBase("192.168.2.0", "255.255.255.0");
    Ipv4InterfaceContainer apEbInterface = address.Assign(apEbDevice);
    Ipv4InterfaceContainer staEbInterface = address.Assign(staEbDevice);

    ApplicationContainer sinkDbApps, sourceDbApps, sinkEbApps, sourceEbApps;   // per-STA sinks on each AP
    uint32_t portDb = 9;
    uint32_t portEb = 100;

    // AP addresses 
    auto ipv4Db = apDbNode.Get(0)->GetObject<Ipv4>();
    Ipv4Address apDbAddr = ipv4Db->GetAddress(1, 0).GetLocal();

    auto ipv4Eb = apEbNode.Get(0)->GetObject<Ipv4>();
    Ipv4Address apEbAddr = ipv4Eb->GetAddress(1, 0).GetLocal();

    // DB: create N sinks on AP_DB (each unique port)
    for (uint32_t i = 0; i < nDbWifi; ++i)
    {
        InetSocketAddress sinkSocket(apDbAddr, portDb++);

        OnOffHelper onOff("ns3::UdpSocketFactory", sinkSocket);
        onOff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
        onOff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
        onOff.SetConstantRate(offeredRate, payloadSize);
        sourceDbApps.Add(onOff.Install(staDbNodes.Get(i)));

        PacketSinkHelper sinkHelper("ns3::UdpSocketFactory", sinkSocket);
        sinkDbApps.Add(sinkHelper.Install(apDbNode.Get(0)));
    }

    // EB: create N sinks on AP_EB (each unique port)
    for (uint32_t i = 0; i < nEbWifi; ++i)
    {
        InetSocketAddress sinkSocket(apEbAddr, portEb++);

        OnOffHelper onOff("ns3::UdpSocketFactory", sinkSocket);
        onOff.SetAttribute("OnTime", StringValue("ns3::ConstantRandomVariable[Constant=1]"));
        onOff.SetAttribute("OffTime", StringValue("ns3::ConstantRandomVariable[Constant=0]"));
        onOff.SetConstantRate(offeredRate, payloadSize);
        sourceEbApps.Add(onOff.Install(staEbNodes.Get(i)));

        PacketSinkHelper sinkHelper("ns3::UdpSocketFactory", sinkSocket);
        sinkEbApps.Add(sinkHelper.Install(apEbNode.Get(0)));
    }

    PopulateARPcache();

    sinkDbApps.Start(Seconds(0.0));
    sinkEbApps.Start(Seconds(0.0));
    sinkDbApps.Stop(Seconds(simulationTime + 1));
    sinkEbApps.Stop(Seconds(simulationTime + 1));

    // Staggered Startup, first all DbSta start transmiting then EbSta
    for (uint32_t i = 0; i < sourceDbApps.GetN(); ++i)
    {
        Ptr<Application> app = sourceDbApps.Get(i);
        app->SetStartTime(Seconds(baseStart + i * gap));
        app->SetStopTime(Seconds(simulationTime + 1));
    }

    for (uint32_t i = 0; i < sourceEbApps.GetN(); ++i)
    {
        Ptr<Application> app = sourceEbApps.Get(i);
        app->SetStartTime(Seconds(baseStart + nDbWifi * gap + i * gap));
        app->SetStopTime(Seconds(simulationTime + 1));
    }

    double tAllstarted = baseStart + (nDbWifi + nEbWifi - 1) * gap;
    double tMeasureStart = tAllstarted + warmup;
    double measureWindow = simulationTime - tMeasureStart;

    
    auto rxDbStart = std::make_shared<uint64_t>(0);
    auto rxEbStart = std::make_shared<uint64_t>(0);

    Simulator::Schedule(Seconds(tMeasureStart), [rxDbStart, rxEbStart, &sinkDbApps, &sinkEbApps]()
    {
        uint64_t sumDb = 0;
        for (uint32_t i = 0; i < sinkDbApps.GetN(); ++i)
        {
            sumDb += DynamicCast<PacketSink>(sinkDbApps.Get(i))->GetTotalRx();
        }
        *rxDbStart = sumDb;

        uint64_t sumEb = 0;
        for (uint32_t i = 0; i < sinkEbApps.GetN(); ++i)
        {
            sumEb += DynamicCast<PacketSink>(sinkEbApps.Get(i))->GetTotalRx();
        }
        *rxEbStart = sumEb;
    });
        

    //PCAP 
    if (pcap)
    {
        phy.SetPcapDataLinkType(WifiPhyHelper::DLT_IEEE802_11_RADIO);
        phy.EnablePcap("coex-ap-db", apDbDevice);
        phy.EnablePcap("coex-ap-eb", apEbDevice);
    }

    Simulator::Stop(Seconds(simulationTime + 1));
    std::clog << std::endl << "Starting simulation... ";

    auto start = std::chrono::high_resolution_clock::now();
    Simulator::Run();

    auto finish = std::chrono::high_resolution_clock::now();
    std::clog << "done!\n";
    std::chrono::duration<double> elapsed = finish - start;
    std::cout << "Elapsed time: " << elapsed.count() << " s\n\n";

    int64_t rxDbEnd = 0;
    for (uint32_t i = 0; i < sinkDbApps.GetN(); ++i)
    {
        rxDbEnd += DynamicCast<PacketSink>(sinkDbApps.Get(i))->GetTotalRx();
    }

    uint64_t rxEbEnd = 0;
    for (uint32_t i = 0; i < sinkEbApps.GetN(); ++i)
    {
        rxEbEnd += DynamicCast<PacketSink>(sinkEbApps.Get(i))->GetTotalRx();
    }

    double thrDbMbps = (rxDbEnd - *rxDbStart) * 8.0 / (measureWindow * 1e6);
    double thrEbMbps = (rxEbEnd - *rxEbStart) * 8.0 / (measureWindow * 1e6);


    // double thrDbMbps = 0.0;
    // for (uint32_t i = 0; i < sinkDbApps.GetN(); ++i)
    // {
    //     uint64_t rxBytes = DynamicCast<PacketSink>(sinkDbApps.Get(i))->GetTotalRx();
    //     thrDbMbps += (rxBytes * 8.0) / (simulationTime * 1e6);
    // }

    // double thrEbMbps = 0.0;
    // for (uint32_t i = 0; i < sinkEbApps.GetN(); ++i)
    // {
    //     uint64_t rxBytes = DynamicCast<PacketSink>(sinkEbApps.Get(i))->GetTotalRx();
    //     thrEbMbps += (rxBytes * 8.0) / (simulationTime * 1e6);
    // }

    std::cout << "Results:\n";
    std::cout << "- Throughput BSS_DB: " << thrDbMbps << " Mbit/s\n";
    std::cout << "- Throughput BSS_EB: " << thrEbMbps << " Mbit/s\n";

    Simulator::Destroy();
    return 0;
}

static std::string BuildTxopFilename(const std::string& prefix)
{
    std::ostringstream oss;
    oss << prefix
        << "-" << trace_nDbWifi
        << "-" << trace_nEbWifi
        << "-" << (trace_enableRts ? 1 : 0)
        << ".csv";
    return oss.str();
}

static void TxopTraceDb(uint32_t nodeId, Time start, Time duration, uint8_t linkId, bool failed)
{
    static std::ofstream out(BuildTxopFilename("txop-trace-db"), std::ios::app);
    out << Simulator::Now().GetSeconds() << ","
        << nodeId << ","
        << start.GetNanoSeconds() << ","
        << duration.GetNanoSeconds() << ","
        << failed << std::endl;
}

static void TxopTraceEb(uint32_t nodeId, Time start, Time duration, uint8_t linkId, bool failed)
{
    static std::ofstream out(BuildTxopFilename("txop-trace-eb"), std::ios::app);
    out << Simulator::Now().GetSeconds() << ","
        << nodeId << ","
        << start.GetNanoSeconds() << ","
        << duration.GetNanoSeconds() << ","
        << failed << std::endl;
}

void LogIpt(uint32_t nodeId, uint8_t linkId, uint32_t ipt)
{
    static std::ofstream out("ipt-backoff-trace.csv", std::ios::app);
    out << Simulator::Now().GetSeconds() << "," << nodeId  << "," << ipt << std::endl;
}

void LogInitialBackoff(uint32_t nodeId, uint8_t linkId, uint32_t backoff)
{
    static std::ofstream out("initial-backoff-trace.csv", std::ios::app);
    out << Simulator::Now().GetSeconds() << "," << nodeId << "," << backoff << std::endl;
}

void LogDeterministicBackoff(uint32_t nodeId, uint8_t linkId, uint32_t backoff)
{
    static std::ofstream out("deterministic-backoff-trace.csv", std::ios::app);
    out << Simulator::Now().GetSeconds() << "," << nodeId << "," << backoff << std::endl;
}

void LogIntermediateBackoff(uint32_t nodeId, uint8_t linkId,  uint32_t backoff)
{
    static std::ofstream out("intermediate-backoff-trace.csv", std::ios::app);
    out << Simulator::Now().GetSeconds() << "," << nodeId << "," << backoff << std::endl;
}

void LogBackoff(uint32_t nodeId, uint8_t linkId,  uint32_t backoff)
{
    static std::ofstream out("backoff-trace.csv", std::ios::app);
    out << Simulator::Now().GetSeconds() << "," << nodeId << "," << backoff << std::endl;
}