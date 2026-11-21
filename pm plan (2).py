
import xlsxwriter
from datetime import datetime, timedelta

class ProjectPlanGenerator:
    def __init__(self):
        self.workbook = xlsxwriter.Workbook('EarthSuit_Project_Plan.xlsx')
        self.setup_formats()
        
    def setup_formats(self):
        """Create formatting styles"""
        self.header_format = self.workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1
        })
        
        self.subheader_format = self.workbook.add_format({
            'bold': True,
            'bg_color': '#DCE6F1',
            'border': 1
        })
        
        self.task_format = self.workbook.add_format({
            'border': 1
        })
        
        self.milestone_format = self.workbook.add_format({
            'bold': True,
            'bg_color': '#FFC000',
            'border': 1
        })
        
    def create_overview(self):
        """Create project overview sheet"""
        sheet = self.workbook.add_worksheet('Project Overview')
        
        # Set column widths
        sheet.set_column('A:A', 40)
        sheet.set_column('B:D', 15)
        
        # Headers
        headers = ['Project Component', 'Start Date', 'Duration (Days)', 'Budget ($)']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)
        
        # Major components
        components = [
            ('1. Project Initialization', '2024-01-15', 30, 50000),
            ('2. Design Phase', '2024-02-15', 60, 150000),
            ('3. Prototype Development', '2024-04-15', 90, 300000),
            ('4. Testing & Validation', '2024-07-15', 60, 200000),
            ('5. Manufacturing Setup', '2024-09-15', 90, 500000),
            ('6. Production Launch', '2024-12-15', 30, 400000)
        ]
        
        for row, (component, start, duration, budget) in enumerate(components, 1):
            sheet.write(row, 0, component, self.subheader_format)
            sheet.write(row, 1, start, self.task_format)
            sheet.write(row, 2, duration, self.task_format)
            sheet.write(row, 3, budget, self.task_format)

    def create_task_breakdown(self):
        """Create detailed task breakdown"""
        sheet = self.workbook.add_worksheet('Task Breakdown')
        
        # Set column widths
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:G', 15)
        
        # Headers
        headers = ['ID', 'Task', 'Start Date', 'Duration', 'Resources', 'Dependencies', 'Status']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)
        
        tasks = [
            # Project Initialization
            ('1.1', 'Requirements Analysis', '2024-01-15', 15, 'Project Manager, Engineers', '-', 'Planning'),
            ('1.2', 'Team Assembly', '2024-01-20', 20, 'HR, Project Manager', '1.1', 'Planning'),
            
            # Design Phase
            ('2.1', 'Fresnel Lens Design', '2024-02-15', 30, 'Optical Engineers', '1.2', 'Planning'),
            ('2.2', 'Cooling System Design', '2024-02-15', 30, 'Thermal Engineers', '1.2', 'Planning'),
            ('2.3', 'Power System Design', '2024-02-15', 30, 'Electrical Engineers', '1.2', 'Planning'),
            ('2.4', 'Control System Design', '2024-03-15', 30, 'Software Engineers', '2.1,2.2,2.3', 'Planning'),
            
            # Prototype Development
            ('3.1', 'Component Fabrication', '2024-04-15', 45, 'Manufacturing Team', '2.4', 'Planning'),
            ('3.2', 'Assembly Integration', '2024-05-30', 30, 'Integration Team', '3.1', 'Planning'),
            ('3.3', 'Initial Testing', '2024-06-30', 15, 'Test Engineers', '3.2', 'Planning'),
            
            # Testing & Validation
            ('4.1', 'Performance Testing', '2024-07-15', 30, 'Test Engineers', '3.3', 'Planning'),
            ('4.2', 'Environmental Testing', '2024-08-15', 20, 'Test Engineers', '4.1', 'Planning'),
            ('4.3', 'Safety Certification', '2024-09-01', 20, 'Quality Team', '4.2', 'Planning'),
            
            # Manufacturing Setup
            ('5.1', 'Facility Setup', '2024-09-15', 45, 'Operations Team', '4.3', 'Planning'),
            ('5.2', 'Equipment Installation', '2024-10-30', 30, 'Operations Team', '5.1', 'Planning'),
            ('5.3', 'Process Validation', '2024-11-30', 15, 'Quality Team', '5.2', 'Planning'),
            
            # Production Launch
            ('6.1', 'Pilot Production', '2024-12-15', 15, 'Production Team', '5.3', 'Planning'),
            ('6.2', 'Quality Verification', '2024-12-30', 10, 'Quality Team', '6.1', 'Planning'),
            ('6.3', 'Full Production Launch', '2025-01-10', 5, 'All Teams', '6.2', 'Planning')
        ]
        
        for row, task in enumerate(tasks, 1):
            for col, value in enumerate(task):
                sheet.write(row, col, value, self.task_format)

    def create_resource_allocation(self):
        """Create resource allocation sheet"""
        sheet = self.workbook.add_worksheet('Resource Allocation')
        
        # Set column widths
        sheet.set_column('A:A', 30)
        sheet.set_column('B:F', 15)
        
        # Headers
        headers = ['Resource', 'Count', 'Cost/Hour ($)', 'Hours/Week', 'Total Cost ($)']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)
        
        resources = [
            ('Project Manager', 1, 75, 40, '=B2*C2*D2*52'),
            ('Optical Engineers', 3, 65, 40, '=B3*C3*D3*52'),
            ('Thermal Engineers', 3, 65, 40, '=B4*C4*D4*52'),
            ('Electrical Engineers', 4, 65, 40, '=B5*C5*D5*52'),
            ('Software Engineers', 3, 70, 40, '=B6*C6*D6*52'),
            ('Manufacturing Team', 10, 45, 40, '=B7*C7*D7*52'),
            ('Integration Team', 5, 55, 40, '=B8*C8*D8*52'),
            ('Test Engineers', 4, 60, 40, '=B9*C9*D9*52'),
            ('Quality Team', 3, 50, 40, '=B10*C10*D10*52'),
            ('Operations Team', 6, 45, 40, '=B11*C11*D11*52')
        ]
        
        for row, resource in enumerate(resources, 1):
            for col, value in enumerate(resource):
                sheet.write(row, col, value, self.task_format)

    def create_component_tracking(self):
        """Create component tracking sheet"""
        sheet = self.workbook.add_worksheet('Component Tracking')
        
        # Set column widths
        sheet.set_column('A:A', 40)
        sheet.set_column('B:G', 15)
        
        # Headers
        headers = ['Component', 'Quantity', 'Unit Cost ($)', 'Lead Time (days)', 'Supplier', 'Quality Check', 'Status']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)
        
        components = [
            # Fresnel Lens System
            ('Fresnel Lens Array', 100, 85, 45, 'OpticalCo', 'Focus Test', 'Ordered'),
            ('Lens Mount Assembly', 100, 25, 30, 'MechTech', 'Alignment', 'Pending'),
            
            # Cooling System
            ('Peltier Modules', 600, 12, 30, 'CoolTech', 'Thermal Test', 'Ordered'),
            ('Heat Sinks', 600, 8, 20, 'ThermalPro', 'Fit Check', 'Ordered'),
            ('Thermal Paste', 1000, 2, 15, 'ThermalPro', 'Consistency', 'In Stock'),
            
            # Power System
            ('Supercapacitors', 1800, 15, 35, 'PowerTech', 'Capacity Test', 'Ordered'),
            ('Power Controllers', 100, 175, 40, 'ElectroCo', 'Function Test', 'Pending'),
            ('Battery Packs', 100, 120, 45, 'BatteryTech', 'Charge Test', 'Ordered'),
            
            # Control System
            ('MCU Boards', 100, 45, 30, 'ElectroCo', 'Program Test', 'Pending'),
            ('Sensors', 800, 8, 25, 'SensorTech', 'Calibration', 'Ordered'),
            ('Display Units', 100, 25, 30, 'DisplayCo', 'Visual Test', 'Pending')
        ]
        
        for row, component in enumerate(components, 1):
            for col, value in enumerate(component):
                sheet.write(row, col, value, self.task_format)

    def create_risk_register(self):
        """Create risk register sheet"""
        sheet = self.workbook.add_worksheet('Risk Register')
        
        # Set column widths
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 40)
        sheet.set_column('C:G', 15)
        
        # Headers
        headers = ['ID', 'Risk Description', 'Probability', 'Impact', 'Mitigation Strategy', 'Owner', 'Status']
        for col, header in enumerate(headers):
            sheet.write(0, col, header, self.header_format)
        
        risks = [
            ('R1', 'Component supply chain delay', 'Medium', 'High', 'Multiple suppliers', 'Procurement', 'Monitoring'),
            ('R2', 'Thermal performance issues', 'Low', 'High', 'Enhanced testing', 'Engineering', 'Mitigated'),
            ('R3', 'Power system integration', 'Medium', 'High', 'Modular design', 'Engineering', 'Active'),
            ('R4', 'Software bugs', 'Medium', 'Medium', 'Extensive testing', 'Software', 'Active'),
            ('R5', 'Cost overrun', 'Medium', 'High', 'Regular reviews', 'Project Manager', 'Monitoring'),
            ('R6', 'Certification delays', 'Low', 'High', 'Early engagement', 'Quality', 'Planned'),
            ('R7', 'Production yield issues', 'Medium', 'High', 'Pilot run', 'Operations', 'Planned')
        ]
        
        for row, risk in enumerate(risks, 1):
            for col, value in enumerate(risk):
                sheet.write(row, col, value, self.task_format)

    def generate_plan(self):
        """Generate complete project plan"""
        self.create_overview()
        self.create_task_breakdown()
        self.create_resource_allocation()
        self.create_component_tracking()
        self.create_risk_register()
        self.workbook.close()

if __name__ == "__main__":
    planner = ProjectPlanGenerator()
    planner.generate_plan()
    print("Project plan has been generated: EarthSuit_Project_Plan.xlsx")
