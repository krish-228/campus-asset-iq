// Sample Data for PSM Hospital Device Tracker
// Exclusively configured for PSM Hospital Healthcare Facility (Single Facility, 7 Levels: Basement, Ground Floor, and 5 Upper Clinical Floors).

const INITIAL_SAMPLE_DATA = {
    organizations: [
        { id: "HOSP", name: "PSM Hospital", type: "Healthcare", color: "emerald" }
    ],

    buildings: [
        // PSM Hospital Single Facility Complex
        { id: "bldg-hosp-main", orgId: "HOSP", name: "PSM Hospital", code: "PSM-MAIN" }
    ],

    floors: [
        // 7 Facility Levels: Basement (-1), Ground (0), 1st to 5th Floors (1..5)
        { 
            id: "fl-basement", 
            buildingId: "bldg-hosp-main", 
            name: "Basement Floor (Biomedical & IT Server Hub)", 
            shortName: "Basement", 
            code: "B", 
            number: -1, 
            icon: "server", 
            dept: "Biomedical Engineering Workshop, Telemetry Hub & Central Stores" 
        },
        { 
            id: "fl-gf", 
            buildingId: "bldg-hosp-main", 
            name: "Ground Floor (Emergency, Triage & Radiology)", 
            shortName: "Ground Floor", 
            code: "GF", 
            number: 0, 
            icon: "ambulance", 
            dept: "Emergency & Trauma Triage, Registration, Billing & Radiology Imaging" 
        },
        { 
            id: "fl-1", 
            buildingId: "bldg-hosp-main", 
            name: "1st Floor (Outpatient Department - OPD)", 
            shortName: "1st Floor", 
            code: "1F", 
            number: 1, 
            icon: "stethoscope", 
            dept: "Specialist Consultation Clinics, Doctor Cabins & Central Pharmacy" 
        },
        { 
            id: "fl-2", 
            buildingId: "bldg-hosp-main", 
            name: "2nd Floor (ICU Complex & Critical Care)", 
            shortName: "2nd Floor", 
            code: "2F", 
            number: 2, 
            icon: "heart-pulse", 
            dept: "Intensive Care Units (ICU/CCU), Bedside Monitoring & Central Nursing Hub" 
        },
        { 
            id: "fl-3", 
            buildingId: "bldg-hosp-main", 
            name: "3rd Floor (Operation Theatres & PACU)", 
            shortName: "3rd Floor", 
            code: "3F", 
            number: 3, 
            icon: "scissors", 
            dept: "Modular Surgical Theatres (OT-1, OT-2) & Post-Anesthesia Recovery (PACU)" 
        },
        { 
            id: "fl-4", 
            buildingId: "bldg-hosp-main", 
            name: "4th Floor (Inpatient Deluxe & Medical Wards)", 
            shortName: "4th Floor", 
            code: "4F", 
            number: 4, 
            icon: "bed", 
            dept: "Inpatient Care Suites, Deluxe Recovery Rooms & Step-Down Telemetry" 
        },
        { 
            id: "fl-5", 
            buildingId: "bldg-hosp-main", 
            name: "5th Floor (Pathology Labs & Blood Bank)", 
            shortName: "5th Floor", 
            code: "5F", 
            number: 5, 
            icon: "microscope", 
            dept: "Clinical Biochemistry, Automated Hematology, Blood Bank & Medical Admin" 
        }
    ],

    rooms: [
        // Basement Rooms
        { id: "rm-bme-lab", floorId: "fl-basement", roomNumber: "B-01", name: "Biomedical Engineering Workshop", type: "Engineering Lab" },
        { id: "rm-server-room", floorId: "fl-basement", roomNumber: "B-02", name: "Hospital IT Server & Telemetry Hub", type: "Server Hub" },

        // Ground Floor Rooms
        { id: "rm-hosp-triage", floorId: "fl-gf", roomNumber: "G-01", name: "Emergency & Trauma Triage Desk 01", type: "Emergency Station" },
        { id: "rm-diag-ct", floorId: "fl-gf", roomNumber: "G-02", name: "CT / MRI Diagnostic Console 01", type: "Medical Imaging" },
        { id: "rm-diag-xray", floorId: "fl-gf", roomNumber: "G-03", name: "Digital X-Ray Diagnostic Station", type: "Diagnostic Room" },

        // 1st Floor Rooms (OPD)
        { id: "rm-opd-c1", floorId: "fl-1", roomNumber: "101", name: "OPD Consultation Room 104", type: "Doctor Cabin" },
        { id: "rm-opd-bill", floorId: "fl-1", roomNumber: "102", name: "OPD Registration & Billing 02", type: "Billing Counter" },
        { id: "rm-pharmacy", floorId: "fl-1", roomNumber: "103", name: "Central Hospital Pharmacy Counter", type: "Pharmacy Desk" },

        // 2nd Floor Rooms (ICU)
        { id: "rm-hosp-icu1", floorId: "fl-2", roomNumber: "201", name: "ICU Bedside Monitoring Pod A", type: "Critical Care" },
        { id: "rm-hosp-icu2", floorId: "fl-2", roomNumber: "202", name: "ICU Central Nursing Telemetry Station", type: "Nurse Station" },

        // 3rd Floor Rooms (OT)
        { id: "rm-ot-1", floorId: "fl-3", roomNumber: "301", name: "Modular Operation Theatre OT-1", type: "Surgical Theatre" },
        { id: "rm-pacu", floorId: "fl-3", roomNumber: "302", name: "PACU Post-Anesthesia Recovery Hub", type: "Recovery Ward" },

        // 4th Floor Rooms (Inpatient Wards)
        { id: "rm-ward-4a", floorId: "fl-4", roomNumber: "401", name: "Inpatient Deluxe Ward Station 4A", type: "Inpatient Ward" },
        { id: "rm-stepdown", floorId: "fl-4", roomNumber: "402", name: "Step-Down Telemetry Desk", type: "Monitoring Desk" },

        // 5th Floor Rooms (Pathology & Blood Bank)
        { id: "rm-path-bio", floorId: "fl-5", roomNumber: "501", name: "Automated Biochemistry Analyzer Desk", type: "Medical Lab" },
        { id: "rm-blood-bank", floorId: "fl-5", roomNumber: "502", name: "Central Blood Bank & Cryo-Storage", type: "Blood Bank" }
    ],

    users: [],


    devices: [],
    locationHistories: [],
    assignmentHistories: [],
    loginSessions: []
};
