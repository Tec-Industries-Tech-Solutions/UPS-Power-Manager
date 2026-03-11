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

        //Define variables
        String tempUnit;
        String upsIP;
        String upsPort;
        int refreshTime;
        int batteryLowPowerThreshold;
        String batteryLowPower="No";
        String batteryFailure = "No";
        double batteryTempThreshold;
        String batteryOverHeat = "No";

        // Use try-with-resources for Scanner (IDE hint resolved)
        try (Scanner input = new Scanner(System.in)) {
            System.out.println("Enter temperature unit (C, K, or F):");
            tempUnit = input.nextLine();

            System.out.println("Enter UPS IP address:");
            upsIP = input.nextLine();

            System.out.println("Enter UPS port:");
            upsPort = input.nextLine();

            System.out.println("Enter refresh time in seconds:");
            refreshTime = input.nextInt();
            
            System.out.println("Enter Low power threshold");
            batteryLowPowerThreshold = input.nextInt();
        
            System.out.println("Enter tempature threshold");
            batteryTempThreshold = input.nextInt();
        } 

        
        // Normalize input
        tempUnit = tempUnit.toUpperCase().substring(0, 1);

        boolean changeF = false;
        boolean changeK = false;

        if (!tempUnit.equals("C") && !tempUnit.equals("F") && !tempUnit.equals("K")) {
            System.out.println("Invalid temperature unit, defaulting to C");
            tempUnit = "C";
        }

        if (tempUnit.equals("F")) {
            changeF = true;
        }

        if (tempUnit.equals("K")) {
            changeK = true;
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

                    //Get UPS data
                    int batteryCharge = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.4.0");
                    int batteryTempC = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.7.0");
                    int batteryUptimecs = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.8.0");
                    int upsLoad = getInt(snmp, target, "1.3.6.1.2.1.33.1.4.4.1.5.1");
                    int batteryTimeRemaining = getInt(snmp, target, "1.3.6.1.2.1.33.1.2.3.0");
                    for (int i = 1; i <= 20; i++) {
                        String alarm = getString(snmp, target, "1.3.6.1.2.1.33.1.6.2.1.2." + i);

                        if (alarm == null) continue;

                        if (alarm.equals("upsAlarmBatteryBad")) {
                        batteryFailure = "Yes";
                        }
                    }

                    // Convert centiseconds → seconds
                    int batteryUptimeSeconds = batteryUptimecs / 100;

                    // Break into time units
                    int years = batteryUptimeSeconds / 31536000;
                    batteryUptimeSeconds %= 31536000;
                    int yearsBT = batteryTimeRemaining / 525600;
                    batteryTimeRemaining %= 525600;

                    int days = batteryUptimeSeconds / 86400;
                    batteryUptimeSeconds %= 86400;
                    int daysBT = batteryTimeRemaining / 1440;
                    batteryTimeRemaining %= 1440;

                    int hours = batteryUptimeSeconds / 3600;
                    batteryUptimeSeconds %= 3600;
                    int hoursBT = batteryTimeRemaining / 60;
                    batteryTimeRemaining %= 60;

                    int minutes = batteryUptimeSeconds / 60;
                    int minutesBT = batteryTimeRemaining;

                    int seconds = batteryUptimeSeconds % 60;
                    
                    double tempCompare ;

                    String tempDisplay;
                    if (changeF) {
                        double batteryTempF = (batteryTempC * 9 / 5) + 32;
                        tempDisplay = batteryTempF + "°F";
                        tempCompare = batteryTempF;
                        
                    } else if (changeK) {
                        double batteryTempK = (batteryTempC + 273.15);
                        tempDisplay = batteryTempK + "°K";
                        tempCompare = batteryTempK;
                    } else {
                        tempDisplay = batteryTempC + "°C";
                        tempCompare = batteryTempC;
                    }

                    //Check if battery is low
                    if (batteryCharge <= batteryLowPowerThreshold){
                        batteryLowPower = "Yes";
                    }

                    //Check if battery is too hot
                    if (tempCompare >= batteryTempThreshold){
                        batteryOverHeat = "Yes";
                    }
                    //Print values
                    //Monitoring
                    System.out.println("-----------------------------");
                    System.out.println("Battery Charge: " + batteryCharge + "%");
                    System.out.println("Battery Temp: " + tempDisplay); 
                    System.out.println("Time on Battery: " + years + "y " + days + "d " + hours + "h " + minutes + "m " + seconds + "s");
                    System.out.println("Time Remaing on Battery: " + yearsBT + "y " + daysBT + "d " + hoursBT + "h " + minutesBT + "m ");
                    System.out.println("UPS Load: " + upsLoad + "%");
                    //Warnings
                    System.out.println("Battery Low Power: " + batteryLowPower);
                    System.out.println("Battery Failure: " + batteryFailure);
                    System.out.println("Battery too hot: " + batteryOverHeat);

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

        // Prevent crashes on missing OIDs
        if (value.equalsIgnoreCase("noSuchInstance") ||
            value.equalsIgnoreCase("noSuchObject") ||
            value.equalsIgnoreCase("endOfMibView")) {
            return -1; // sentinel value meaning "missing"
        }

        return Integer.parseInt(value);
    }

    return -1;
}


    private static String getString(Snmp snmp, CommunityTarget<UdpAddress> target, String oid) throws Exception { 
        PDU pdu = new PDU(); 
        pdu.add(new VariableBinding(new OID(oid))); 
        pdu.setType(PDU.GET); 
        
        ResponseEvent<UdpAddress> response = snmp.get(pdu, target); 
        
        if (response != null && response.getResponse() != null) { 
            VariableBinding vb = response.getResponse().get(0); 
            String value = vb.getVariable().toString(); 
            
            // Handle missing OIDs 
            if (value.equalsIgnoreCase("noSuchInstance") || 
                value.equalsIgnoreCase("noSuchObject") || 
                value.equalsIgnoreCase("endOfMibView")) { 
                return null; 
            } 
            
            return value; 
        } 
        
        return null; 
    }
    
}
