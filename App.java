package com.jadon.ups;

import java.util.Scanner;
import java.util.concurrent.TimeUnit;

import org.snmp4j.CommunityTarget;
import org.snmp4j.PDU;
import org.snmp4j.Snmp;
import org.snmp4j.event.ResponseEvent;
import org.snmp4j.mp.SnmpConstants;
import org.snmp4j.smi.OID;
import org.snmp4j.smi.OctetString;
import org.snmp4j.smi.UdpAddress;
import org.snmp4j.smi.VariableBinding;
import org.snmp4j.transport.DefaultUdpTransportMapping;

public class App {

    public static void main(String[] args) throws Exception {

        String tempUnit;
        String upsIP;
        String upsPort;
        int refreshTime;

        // Use try-with-resources for Scanner (IDE hint resolved)
        try (Scanner input = new Scanner(System.in)) {
            System.out.println("Enter temperature unit (C or F):");
            tempUnit = input.nextLine();

            System.out.println("Enter UPS IP address:");
            upsIP = input.nextLine();

            System.out.println("Enter UPS port:");
            upsPort = input.nextLine();

            System.out.println("Enter refresh time in seconds:");
            refreshTime = input.nextInt();
        }
        
        // Normalize input
        tempUnit = tempUnit.toUpperCase().substring(0, 1);

        boolean change = false;

        if (!tempUnit.equals("C") && !tempUnit.equals("F")) {
            System.out.println("Invalid temperature unit, defaulting to C");
            tempUnit = "C";
        }

        if (tempUnit.equals("F")) {
            change = true;
        }

        System.out.println("Using temperature unit: " + tempUnit);

        String community = "fake-ups";

        try (DefaultUdpTransportMapping transport = new DefaultUdpTransportMapping()) {
            transport.listen();

            CommunityTarget<UdpAddress> target = new CommunityTarget<>();
            target.setCommunity(new OctetString(community));
            target.setAddress(new UdpAddress(upsIP + "/" + upsPort));
            target.setRetries(2);
            target.setTimeout(1500);
            target.setVersion(SnmpConstants.version2c);

            try (Snmp snmp = new Snmp(transport)) {

                System.out.println("\nStarting live UPS monitoring...\n");

                while (true) {

                    int batteryCharge = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.4.0");
                    int batteryTempC = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.7.0");
                    int batteryUptimecs = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.8.0");
                    int upsLoad = getInt(snmp, target, "1.3.6.1.2.1.33.1.4.4.1.5");

                    // Convert centiseconds → seconds
                    int batteryUptimeSeconds = batteryUptimecs / 100;

                    // Break into time units
                    int years = batteryUptimeSeconds / 31536000;
                    batteryUptimeSeconds %= 31536000;

                    int days = batteryUptimeSeconds / 86400;
                    batteryUptimeSeconds %= 86400;

                    int hours = batteryUptimeSeconds / 3600;
                    batteryUptimeSeconds %= 3600;

                    int minutes = batteryUptimeSeconds / 60;
                    int seconds = batteryUptimeSeconds % 60;

                    String tempDisplay;
                    if (change) {
                        int batteryTempF = (batteryTempC * 9 / 5) + 32;
                        tempDisplay = batteryTempF + "°F";
                    } else {
                        tempDisplay = batteryTempC + "°C";
                    }

                    //Print values
                    System.out.println("-----------------------------");
                    System.out.println("Battery Charge: " + batteryCharge + "%");
                    System.out.println("Battery Temp: " + tempDisplay); 
                    System.out.println("Time on Battery: " + years + "y " + days + "d " + hours + "h " + minutes + "m " + seconds + "s");
                    System.out.println("UPS Load: " + upsLoad + "%");

                    // Intentional sleep to control polling rate (IDE warning resolved)
                    TimeUnit.SECONDS.sleep(refreshTime);
                }
            }
        }
    }

    private static int getInt(Snmp snmp, CommunityTarget<UdpAddress> target, String oid) throws Exception {
        PDU pdu = new PDU();
        pdu.add(new VariableBinding(new OID(oid)));
        pdu.setType(PDU.GET);

        ResponseEvent<UdpAddress> response = snmp.get(pdu, target);

        if (response != null && response.getResponse() != null) {
            String value = response.getResponse().get(0).getVariable().toString();
            return Integer.parseInt(value);
        }

        return -1;
    }
}
