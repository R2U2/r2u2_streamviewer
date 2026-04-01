#!/usr/bin/env python3
#
import os
import numpy as np
import sys

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QGridLayout, QHBoxLayout,
    QPushButton, QComboBox, QTextEdit, QTableWidget, QGroupBox,
    QTableWidgetItem, QHeaderView, QMessageBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from scipy.special import erfinv

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

#from gui import MainWindow, AnotherWindow
#
# Ashley Behrendt
# January 14, 2026
# R2U2 Stream Viewer Visualization Tool
# VSM Cooperative Agreement
#
'''
The purpose of this file is to generate a GUI for thean individual R2U2 stream.

The following ASCII art is the expected output for the GUI.

The data used to test the GUI is sourced from the R2U2 Playground website. The output
is generated using the "Temporal" example from the website. (https://r2u2.temporallogic.org/playground/)

For additional notes and details, please reference "R2U2_streamviewer_notes.txt"
'''

# The primary modiles for Qt are QtWidgets, QtGui, and QtCore
class AnotherWindow(QMainWindow):
    '''
    GUI window for additional heatmap windows to visualize timeline.

    This class manages:
    - Opening a new window
    - Creates a layout for the heatmap window

    The heatmap displays timeline data (boolean values) over time
    for selected contracts or task groupings. 
    '''
    def __init__(self, contract, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Status")
        self.resize(1500, 900)

        label = QLabel(f"{contract} Data Status")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(30)
        font.setBold(True)
        label.setFont(font)

        self.another_central_widget = QWidget()
        self.another_layout = QGridLayout(self.another_central_widget)
        self.another_layout.addWidget(label,0,1)
        self.setCentralWidget(self.another_central_widget)

        pass
    
class ReportWindow(QMainWindow):
    '''
    GUI window for pdf report generation window to request user input
    for the statistical analysis report.

    This class manages:
    - Opening a new window for the pdf report
    - Creates a layout for the report generation input

    The user input is dynamically added to an html file to generate
    a pdf report for the statistical analysis tool. 
    '''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Report Generation")
        self.resize(800,500)  # x, y, width, height

        label = QLabel("Statistical Analysis Report Generation")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(30)
        font.setBold(True)
        label.setFont(font)

        self.report_central_widget = QWidget()
        self.report_layout = QGridLayout(self.report_central_widget)
        self.report_layout.setAlignment(Qt.AlignCenter)
        self.report_layout.addWidget(label,0, 2)
        self.setCentralWidget(self.report_central_widget)

        pass

class StreamViewer(QMainWindow):
    '''
    Main GUI window for the R2U2 Streamviewer Tool.

    This class manages:
    - Loading and parsing contract and Monte Carlo iteration data
    - Aggregating timeline output data
    - Handling execution and task filtering
    - Rendering interactive heatmap visualizations
    '''
    def __init__(self):
        super().__init__()
        current_directory = os.path.dirname(os.path.abspath(__file__))
        self.contracts_dict = self.read_contracts(os.path.join(current_directory, "demos/data/contracts.txt"))
        self.uuid_dict = self.read_uuid(os.path.join(current_directory, "demos/data/contracts.txt"))
        self.data_by_iter = {}  # key: iteration number, value: data_dict
        output_files = sorted(
            f for f in os.listdir(os.path.join(current_directory, "demos/data")) if f.startswith("output_iter")
        )

        for i, file in enumerate(output_files):
            file_path = os.path.join(current_directory, "demos/data", file)
            self.data_by_iter[i + 1] = self.read_output(file_path, self.contracts_dict)
            pass

        self.num_mc_iter = len(output_files)

        if self.num_mc_iter == 0:
            # No data files found
            self.data_dict = {c: [] for c in self.contracts_dict}
            pass
        else:
            # Start with cumulative data
            self.data_dict = self.get_data_for_iteration(0)  # 0 = cumulative
            pass

        self.p_hat_dict = self.calc_proportion(self.data_dict)[0]
        self.num_samples_dict = self.calc_proportion(self.data_dict)[1]
        self.failed_times_dict = self.calc_times(self.data_dict)[0]
        self.passed_times_dict = self.calc_times(self.data_dict)[1]
        self.setup_central_widget()
        self.build_layouts()

        self.current_data_dict = self.data_dict.copy()
        self.current_p_hat_dict, self.current_num_samples_dict = self.calc_proportion(self.current_data_dict)
        self.current_failed_times_dict, self.current_passed_times_dict = self.calc_times(self.current_data_dict)

        # Build the columns of the GUI
        self.build_left_column()
        self.build_right_column()
        pass
    
    
    def setup_central_widget(self):
        '''
        Construct the main GUI layout.

        Creates:
        - Title label
        - Iteration selection dropdown box (combination box)
        - Task/contract filter dropdown box (combination box)
        - Tables for various statistical analysis points

        Connects user interface signals to their corresponding handlers.
        '''
        self.resize(1200, 900) # Make the window larger
        self.setWindowTitle("R2U2 OUTPUT STREAM VIEWER") # GUI Title
        
        # --------- CENTRAL WIDGET/WINDOW ---------
        # Central Widget is the main window:
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Set Layout:
        self.main_layout = QGridLayout() # Grid will allow us to pick where widgets are
        self.central_widget.setLayout(self.main_layout)

        # ----------------- TITLE -----------------
        title = QLabel("R2U2 OUTPUT STREAM VIEWER")
        title.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(30)
        font.setBold(True)
        title.setFont(font)
        self.main_layout.addWidget(title,0,0,1,2)

        # Add combo box for MC iteration

        # What can we sort by: two combo boxes (iterations, then sort)
        # All iterations as cumulative and individual iterations
        #
        if self.num_mc_iter > 1:
            mc_iter_str_list = ["Cumulative Iterations"] + [f"MC ITERATION {i+1}" for i in range(self.num_mc_iter)]
            pass
        else:
            mc_iter_str_list = [f"MC ITERATION {i+1}" for i in range(self.num_mc_iter)]
            pass
            
        
        uuid_str_list = [f"UUID: {uuid}" for uuid in self.uuid_dict.keys()]
        contracts_str_list = self.contracts_dict
        sort_items = ["ALL CONTRACTS"] + ["ALL UUID"] + uuid_str_list 

        self.mc_iter_combobox = self.create_combobox(
            mc_iter_str_list,
            self.main_layout,
            1,
            0,
            200
            )
        self.sort_combobox = self.create_combobox(
            sort_items,
            self.main_layout, 
            2,
            0,
            300
            )

        # ------------------ REPORT BUTTON --------------------
        report_button = self.create_button(1, 1, "Create Report", None, self.main_layout, None)
        report_button.setFixedSize(200,30)
        report_button.clicked.connect(self.gen_report_window)

        

        self.sort_combobox.currentTextChanged.connect(lambda selection: self.on_sort_changed(selection))
        self.mc_iter_combobox.currentTextChanged.connect(self.on_mc_iter_changed)
        pass
    

    def on_sort_changed(self,selection):
        '''
        Handle changes in UUID/contract filter selection.

        Updates the currently displayed dataset based on the selected filter:
        - ALL CONTRACTS
        - ALL UUID
        - Specific UUID
        - Individual contract

        Parameters
        ----------
        selection : str
            Selected filter value from the combobox.
        '''
        if selection == "ALL CONTRACTS":
            # all contracts will be the full list
            contracts = self.contracts_dict
            pass
        elif selection == "ALL UUID":
            # all uuid will be full list of uuids
            contracts = list(self.uuid_dict.keys())
            pass
        elif selection.startswith("UUID:"):
            # If we are selecting an individual UUID, we need its contracts
            uuid = selection.split(":")[1].strip()
            contracts = self.uuid_dict.get(uuid,[])
            pass
        else:
            # We do not know what contracts will always start with so... else
            contracts = [selection]
            pass

        # Now, we need to pull out the UUID
        if selection == "ALL UUID":
            data_dict_filtered = {}
            for uuid, uuid_contracts in self.uuid_dict.items():
                combined_data = []
                for contract in uuid_contracts:
                    combined_data += self.data_dict[contract]
                    pass
                data_dict_filtered[uuid] = combined_data
                pass
            pass
        else:
            data_dict_filtered = {c: self.data_dict[c] for c in contracts}
            pass

        self.current_data_dict = data_dict_filtered
        self.current_p_hat_dict, self.current_num_samples_dict = self.calc_proportion(data_dict_filtered)
        self.current_failed_times_dict, self.current_passed_times_dict = self.calc_times(data_dict_filtered)
        
        # Update left column tables
        self.refresh_tables(contracts, data_dict_filtered)
        self.refresh_cstat_table(contracts)
        
        return
    def on_mc_iter_changed(self,text):
        '''
        Handle Monte Carlo iteration selection changes.

        Updates the underlying timeline output dataset to reflect either:
          - Cumulative iteration data
          - A specific iteration
        
        Parameters:
        -----------
        text : str
            Selected iteration label from the dropdown box (combination box)
        '''
        if text == "Cumulative Iterations":
            iteration_num = 0
            pass
        else:
            iteration_num = int(text.split()[-1])  # get iteration number
            pass
        # Update the main data_dict for this selection
        self.data_dict = self.get_data_for_iteration(iteration_num)

        # Update current selection if any sort filter is applied
        current_selection = self.sort_combobox.currentText()
        self.on_sort_changed(current_selection)
        return
    
    def refresh_tables(self, contracts, data_dict=None, conf_level=95):
        '''
        Update/refresh the tables on the left column with changed
        data_dict or confidence bound. The user has the ability to adjust the
        data based on the Monte Carlo iteration and groupings of tasks or
        contracts.

        Parameters
        ----------
        contracts : list[str]
            A list of contract names whose statistics should be displayed
            in the tables.

        data_dict : dict[str, list[tuple[str, str]]], optional
            Dictionary mapping contract names to lists of (time, value)
            output data tuples.

        conf_level : int, optional
            Confidence level used when computing Wilson confidence intervals
            for the success proportions. Default is 95.
        '''
        if data_dict is None: # initialization
            data_dict = self.data_dict
            pass

        p_hat_dict, num_samples_dict = self.calc_proportion({c: data_dict[c] for c in contracts})
        failed_times_dict, passed_times_dict = self.calc_times({c: data_dict[c] for c in contracts})

        # ---------------- Contract Success Table ----------------
        if hasattr(self, "cs_table"):
            self.cs_table.setRowCount(len(contracts))
            for row_idx, contract in enumerate(contracts):
                # Contract name
                self.cs_table.setItem(row_idx, 0, QTableWidgetItem(contract))
                # % Passed
                percent = p_hat_dict[contract]*100
                self.cs_table.setItem(row_idx, 1, QTableWidgetItem(f"{percent:.2f}%"))
                # Confidence Interval
                z = self.calc_z(conf_level)
                lb, ub = self.calc_wilson_interval(z, p_hat_dict[contract], num_samples_dict[contract])
                self.cs_table.setItem(row_idx, 2, QTableWidgetItem(f"{lb*100:.2f}%, {ub*100:.2f}%"))
                pass
            pass
                
        # ---------------- Failed Times Table ----------------
        if hasattr(self, "fail_t_table"):
            self.fail_t_table.setRowCount(len(contracts))
            for row_idx, contract in enumerate(contracts):
                self.fail_t_table.setItem(row_idx, 0, QTableWidgetItem(contract))
                unique_times = sorted(set(failed_times_dict[contract]),key=int)
                time_str = ", ".join(unique_times)
                self.fail_t_table.setItem(row_idx, 1, QTableWidgetItem(time_str))
                pass
            pass
        
        # Store current state for other functions
        self.current_data_dict = data_dict
        self.current_p_hat_dict = p_hat_dict
        self.current_num_samples_dict = num_samples_dict
        self.current_failed_times_dict = failed_times_dict
        self.current_passed_times_dict = passed_times_dict
        return

    def refresh_cstat_table(self, contracts):
        '''
        Update/refresh the table on the right column with changed
        data_dict. The user has the ability to adjust the
        data based on the Monte Carlo iteration and groupings of tasks or
        contracts.

        Parameters
        ----------
        contracts : list[str]
            A list of contract names whose statistics should be displayed
            in the tables.
        '''
        # ---------------- Contract Status Table ----------------
        self.cstat_table.clearContents()

        self.cstat_table.setRowCount(len(contracts) + 1) # extra row for all contracts
        for row_idx, contract in enumerate(contracts):
            self.cstat_table.setItem(row_idx, 0, QTableWidgetItem(contract))
            button = self.create_button(row_idx, 1, f"{contract} Data Status", self.cstat_table,None, None)
            button.clicked.connect(lambda checked=False, c=contract: self.open_another_window({c: self.current_data_dict[c]},contract_name=c))
            pass
        
        self.cstat_table.setItem(len(contracts), 0, QTableWidgetItem("ALL SELECTIONS"))
        
        all_button = QPushButton("All Data Status")
        self.cstat_table.setCellWidget(len(contracts), 1, all_button)
        all_button.clicked.connect(lambda checked=False: self.open_another_window(self.current_data_dict,all_selections=True))
        return

    def gen_report_window(self):
        '''
        Generate the report window for the statistical analysis report.
        This window will serve the purpose of taking user input to be dynamically
        added to the html file and converted into a pdf.

        User Input:
            - Name and Date
            - Summary of the analysis being done
            - Description of the criteria for the analysis
            - Strengths and Weaknesses of the analysis
            - Risk Evaluation of the analysis
            - Recommendations for future analyses
        '''
        self.report_window = ReportWindow()

        self.report_window.show()
        self.report_window.raise_()  # Bring to front
        self.report_window.activateWindow()


        # --- Name/Date Input Box ---
        self.name_input_box = self.create_input_box(1,1,1,2, "Enter your name: ", "FIRST LAST", self.report_window.report_layout, 30,300)
        self.date_input_box = self.create_input_box(2,1,2,2, "Enter today's date: ", "MONTH, DAY, YEAR", self.report_window.report_layout, 30,300)
        
        # --- Summary Input Box ---
        self.summary_input_box = self.create_input_box(3,1,3,2, "Please provide a summary \nof what this project/report is analyzing: ", "Please type here...",self.report_window.report_layout, 100, 600)
        self.summary_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        # --- Criteria Input Box ---
        self.criteria_input_box = self.create_input_box(4,1,4,2, "Please describe the required criteria for this analysis.", "Please type here...",self.report_window.report_layout, 100, 600)
        self.criteria_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        # --- Strengths Input Box ---
        self.strengths_input_box = self.create_input_box(5,1,5,2, "Please give the strengths of this timeline.", "Please type here...",self.report_window.report_layout, 100, 600)
        self.strengths_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        # --- Weakenesses Input Box ---
        self.weaknesses_input_box = self.create_input_box(6,1,6,2, "Please give the weaknesses of this timeline.", "Please type here...",self.report_window.report_layout, 100, 600)
        self.weaknesses_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        # --- Risk Evaluation Input Box ---
        self.risk_eval_input_box = self.create_input_box(7,1,7,2, "Please describe potential mission/system\nimpact of failures of this analysis.", "Please type here...",self.report_window.report_layout, 100, 600)
        self.risk_eval_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        self.verdict_input_box = self.create_input_box(8,1,8,2, "Please provide a verdict for this analysis: \nGood / Needs Improvement / Fails Requirements", "Please type here...",self.report_window.report_layout, 100, 600)
        self.verdict_input_box.setLineWrapMode(QTextEdit.WidgetWidth)

        # --- Recommendations Input Box ---
        self.recommendations_input_box = self.create_input_box(9,1,9,2, "Please provide some recommendations \nto improve the timeline for future analysis.", "Please type here...",self.report_window.report_layout, 100, 600)
        self.recommendations_input_box.setLineWrapMode(QTextEdit.WidgetWidth)
        

        # --- Generate PDF Button ---
        pdf_button = self.create_button(10,3,"Generate PDF", None, self.report_window.report_layout, None)
        pdf_button.setFixedSize(200,30)


        pdf_button.clicked.connect(self.generate_pdf_from_inputs)
        return

    def generate_pdf_from_inputs(self):
        '''
        Create a pdf document from the template html file structure,
        user input, and statistical analysis completed in the statistical
        analysis tool.

        There are three major parts to this function:
            - Take user input from the generate pdf window
            - Extract statistical analysis data
            - Dynamically allocate the input and data to the
              template html file and produce a pdf
        '''
        author = self.name_input_box.toPlainText()
        date = self.date_input_box.toPlainText()
        summary = self.summary_input_box.toPlainText()
        criteria = self.criteria_input_box.toPlainText()
        strengths = self.strengths_input_box.toPlainText()
        weaknesses = self.weaknesses_input_box.toPlainText()
        risk_eval = self.risk_eval_input_box.toPlainText()
        verdict = self.verdict_input_box.toPlainText()
        recommendations = self.recommendations_input_box.toPlainText()
        pdf_name = f"Report_{author.replace(' ', '_')}"

        user_inputs = {
            "AUTHOR": author,
            "DATE": date,
            "SUMMARY": summary,
            "CRITERIA": criteria,
            "STRENGTHS": strengths,
            "WEAKNESSES": weaknesses,
            "RISK_EVAL": risk_eval,
            "VERDICT": verdict,
            "RECOMMENDATION": recommendations
        }

        
        # ------------------------------------
        # UUID (Task) Statistics
        # ------------------------------------
        durations = []

        for events in self.data_dict.values():
            times = [int(t) for t, _ in events]
            if times:
                durations.append(max(times) - min(times))
                pass
            pass
        min_duration = min(durations)
        max_duration = max(durations)

        fail_counts_by_uuid = {}

        for uuid, specs in self.uuid_dict.items():
            total_failures = 0
            for spec in specs:
                for _, val in self.data_dict.get(spec, []):
                    if val == "false":
                        total_failures += 1
                        pass
                    pass
                pass
            
            fail_counts_by_uuid[uuid] = total_failures
            pass
        most_failed_task = max(fail_counts_by_uuid, key=fail_counts_by_uuid.get)
        #pdb.set_trace()

        # ------------------------------------
        # Evaluation Statistics
        # ------------------------------------
        total_evals = sum(len(events) for events in self.data_dict.values())
        failed_evals = sum(
            1 for events in self.data_dict.values()
            for _, val in events if val == "false"
        )
        passed_evals = total_evals - failed_evals

        # ------------------------------------
        # Contract Statistics
        # ------------------------------------
        total_contracts = len(self.contracts_dict)
        failed_contracts = sum(
            1 for events in self.data_dict.values()
            if any(val == "false" for _, val in events)
        )
        
        analysis_data = {
            "num_mc_iter": str(self.num_mc_iter),
            "stop_rule": str(1000), # Needs to be replaced
            "timeline_filename": "Timeline Filename", # Needs to be replaced
            "events_per_timeline": str(sum(len(events) for events in self.data_by_iter[1].values())),
            "failed_task_num": str(sum(1 for events in self.data_dict.values() for _, val in events if val =="false")), # across all iterations
            "most_failed_task": most_failed_task,
            "timeline_name": "Timeline Filename", # Needs to be replaced
            "timeline_id": "Timeline ID", # Needs to be replaced
            "filename_ext_and_path": "Timeline Filename", # Needs to be replaced
            "t_start": str(min(int(t) for events in self.data_dict.values() for t, _ in events)),
            "t_end_max": str(max(int(t) for events in self.data_dict.values() for t, _ in events)),
            "t_end_min": str(min(max(int(t) for t,_ in events) for events in self.data_dict.values() if events)),
            "min_duration": str(min_duration),
            "max_duration": str(max_duration),
            "pdf_filename": "Probability Density Function Filename", # Needs to be replaced
            "conf_interval": " 95%",
            "total_contracts": total_contracts,
            "contracts_passed": total_contracts - failed_contracts,
            "contracts_failed": failed_contracts,
            "pass_percent": (total_contracts - failed_contracts)/total_contracts*100,
            "fail_percent": failed_contracts/total_contracts*100,
            "eval_per_iter": total_evals/self.num_mc_iter,
            "total_evals": total_evals,
            "passed_evals": total_evals - failed_evals,
            "failed_evals": failed_evals,
            "passed_percent_evals": ((total_evals - failed_evals)/total_evals*100) if total_evals else 0 ,
            "failed_percent_evals": (failed_evals/total_evals*100) if total_evals else 0 ,      
            }

        # Use jinja2 to dynamically create the tables in the html file:
        env = Environment(loader=FileSystemLoader("demos/statistical_analysis_report"))
        template = env.get_template("statistical_analysis_report.html")

        tasks = []
        for uuid, specs in self.uuid_dict.items():

            failures = 0
            total = 0

            for spec in specs:
                for _, val in self.data_dict.get(spec, []):
                    total += 1
                    if val == "false":
                        failures += 1
                        pass
                    pass
                pass
            

            if total == 0:
                continue

            # Wilson confidence interval approximation
            failure_proportion = failures/total
            p_hat = 1 - failure_proportion
            z = self.calc_z(95)
            lb,ub = self.calc_wilson_interval(z, p_hat, total)

            tasks.append({
                "name": uuid,
                "uuid": uuid,
                "failures": failures,
                "total_evaluations": total,
                "failure_percent": f"{failure_proportion*100:.2f}%",
                "confidence_lower": f"{lb*100:.2f}%",
                "confidence_upper": f"{ub*100:.2f}%"
            })
            pass

        contracts = []

        for contract_name, events in self.data_dict.items():

            total = 0
            failures = 0
            
            for _, val in events:
                total += 1
                if val == "false":
                    failures += 1
                    pass
                pass
            

            if total == 0:
                continue
            

            failure_proportion_contract = failures/total
            p_hat = 1 - failure_proportion_contract
            z = self.calc_z(95)
            lb, ub = self.calc_wilson_interval(z, p_hat, total)
            

            contracts.append({
                "name": contract_name,
                "uuid": "contract",  # replace if you have metadata type stored somewhere
                "failures": failures,
                "total_evaluations": total,
                "failure_percent": f"{failure_proportion_contract*100:.2f}%",
                "confidence_lower": f"{lb*100:.2f}%",
                "confidence_upper": f"{ub*100:.2f}%"
            })
            pass

        context = {}
        context.update(user_inputs)
        context.update(analysis_data)

        context["tasks"] = tasks   # list of task dictionaries
        context["contracts"] = contracts   # list of contract dictionaries

        html_updated_content = template.render(context)
        HTML_FILE = "demos/statistical_analysis_report/html_output_file.html"


        # ------------- Create png of Heat maps for pdf -------------------------
        # We will need a task plot and an all contracts plot
        task_fig = self.create_heatmap(selections=list(self.uuid_dict.keys())) # all uuid
        contract_fig = self.create_heatmap(selections=list(self.data_dict.keys())) # all contracts
        task_path = os.path.join(current_directory, "demos/images", "task_heatmap.png")
        contract_path = os.path.join(current_directory, "demos/images", "contract_heatmap.png")

        task_fig.savefig(task_path, dpi=300)
        contract_fig.savefig(contract_path, dpi=300)

        plt.close(task_fig)
        plt.close(contract_fig)

        # Begin working off statistical_analysi_report.py file:
        #HTML_TEMPLATE = "statistical_analysis_report/statistical_analysis_report.html"
        #HTML_FILE = "statistical_analysis_report/html_output_file.html"
        #with open(HTML_TEMPLATE, "r") as f:
        #    template_content = f.read()
        #    pass
        #html_updated_content = template_content
        #for key, value in user_inputs.items():
        #    html_updated_content = html_updated_content.replace("{{" + key + "}}", value)
        #    pass

        #for key, value in analysis_data.items():
        #    html_updated_content = html_updated_content.replace("{{" + key + "}}", value)
        #    pass

        # Write the changed content from the user input to a NEW file (we dont want to alter the template)
        with open(HTML_FILE, "w") as f:
            f.write(html_updated_content)
            pass

        QMessageBox.information(self.report_window, 
                                "Generating Report", 
                                "Your report is being generated. Please wait...")
        HTML(HTML_FILE).write_pdf(f"{pdf_name}.pdf")
        self.report_window.close()
        QMessageBox.information(None, "Report Generated", f"{pdf_name}.pdf has been successfully generated!\n\nYour report is ready to view!")

        return

    
    def build_layouts(self):
        '''
        Apply left column and right column layout to the main
        layout.
        '''
        self.left_col = QGridLayout()
        self.right_col = QGridLayout()

        self.main_layout.addLayout(self.left_col,3,0)
        self.main_layout.addLayout(self.right_col,3,1)
        pass

    # ----------------------------------------------------------------
    # READ OUTPUT FILES
    # ----------------------------------------------------------------
        
    def read_output(self,filename,contracts):
        '''
        Parse an R2U2 timeline output file.

        Parameters:
        -----------
        filename : str
            Path to output file
        contracts : list[str]
            List of contract names used to initialize the data structure.

        Returns:
        ----------
        dict
            Dictionary mapping contract names to lists of (time, distance) tuples.
        '''
        data = {contract: [] for contract in contracts} # data will be based on the contracts
        with open(filename, "r")as infile:
            for line in infile:
                line = line.strip()
                # Ignore blank lines
                if "" == line:
                    continue


                # Split the line that has format: SPEC: time, bool
                # 1st step: [SPEC] [time, bool]
                contract_str, dat = line.split(":")
                # 2nd step: [time] [boolean]
                time_str, bool_str = dat.split(",")

                if contract_str in data:
                    data[contract_str].append((time_str, bool_str))
                    pass
                else:
                    data[contract_str] = [(time_str, bool_str)]
                pass     
        return data

    def read_uuid(self,filename):
        '''
        Parse a contract file and extract UUID-to-contract mappings.

        Parameters:
        -----------
        filename : str
            Path to contract file

        Returns:
        ----------
        dict
            Dictionary mapping UUID strings to lists of associated contracts.
        '''
        # Sorts contracts by their UUID
        contracts= {}
        inside_spec = False
        with open(filename, "r") as infile:
            for line in infile:
                line = line.strip()

                if line.startswith(("FTSPEC","PTSPEC")):
                    inside_spec = True
                    continue # skip this line
                if inside_spec:
                    if "" == line:
                        continue # blank lines
                    if ":" not in line:
                        continue
                    left,_ = line.split(":",1)
                    uuid, contract = left.split(None,1)
                    contracts.setdefault(uuid, []).append(contract)
                    pass
                pass
            pass
        return contracts

    def read_contracts(self,filename):
        '''
        Parse a contract file and extract contract names.

        Parameters:
        -----------
        filename : str
            Path to contract file

        Returns:
        ----------
        list[str]
            List of contract names
        '''
        # Sorts contracts by their UUID
        contracts= []
        inside_spec = False
        with open(filename, "r") as infile:
            for line in infile:
                line = line.strip()

                if line.startswith(("FTSPEC","PTSPEC")):
                    inside_spec = True
                    continue # skip this line
                if inside_spec:
                    if "" == line:
                        continue # blank lines
                    if ":" not in line:
                        continue
                    left,_ = line.split(":",1)
                    _, contract = left.split(None,1)
                    contracts.append(contract)
                    pass
                pass
            pass
        return contracts

    def get_data_for_iteration(self,iteration):
        '''
        Retrieve R2U2 timeline output data for a specified iteration.
        
        Parameters:
        -----------
        iteration : int
            Iteration number
              - 0 indicates cumulative data across all iterations.
              - Positive integers correspond to individual iterations
       
        Returns:
        ----------
        dict
            Dictionary mapping contract names to lists of (time, distance) tuples.
        '''
        if iteration == 0:
            cumulative_data = {c: [] for c in self.contracts_dict}
            for iter_data in self.data_by_iter.values():
                for c, events in iter_data.items():
                    cumulative_data[c] += events
                    pass
                pass
            return cumulative_data
        else:
            return self.data_by_iter.get(iteration, {})
        pass

    # ----------------------------------------------------------------
    # GUI FEATURES
    # ----------------------------------------------------------------    
    def create_input_box(self, lab_row, lab_column, box_row, box_column, label_text, placeholder_text,layout, height, width):
        '''
        Create an input box to a desired layout.
        
        Parameters:
        -----------
        lab_row, lab_column : int
            Grid position for the label.
        box_row, box_column : int
            Grid position for the text box.
        label_text : str
            Label displayed above or beside the input box.
        placeholder_text : str
            Placeholder text displayed inside the input box.
        layout : QGridLayout
            Layout to which the widgets are added.
        height : int
            Fixed height of the input box.
        width : int
            Fixed width of the input box.
        
        Returns:
        ----------
        input_box
            The created text input widget
        '''
        input_label = QLabel(label_text)
        input_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        input_box = QTextEdit()
        font = QFont()
        font.setPointSize(16)
        
        input_box.setPlaceholderText(placeholder_text)
        input_box.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        input_box.setFixedWidth(width)
        input_box.setFixedHeight(height)
        input_box.setFont(font)
        input_label.setFont(font)
        layout.addWidget(input_label, lab_row, lab_column)
        layout.addWidget(input_box, box_row, box_column)
        return input_box

    def create_table(self,headers,rows,contracts,data):
        '''
        Create a table with desired headers, number of rows, and data.
        
        Parameters:
        -----------
        headers : list[str]
           Header titles for the table.
        rows : int
            Number of rows for placement.
        contracts : list
            contracts to be used in the table
        data : dict
            Output data to be used in the table.
        '''
        # Set the rows and columns
        tableWidget = QTableWidget()

        # Set rows and columns:
        tableWidget.setRowCount(rows)
        tableWidget.setColumnCount(len(headers))
        
        tableWidget.setHorizontalHeaderLabels(headers)
        tableWidget.verticalHeader().setVisible(False)
        
        # Add data to the table:
        # rows will be the output data arranged into a list of strings [SPEC:TIME,BOOL]
        # We want to go through each data set and assign it to a table item.
        # add loop code here:
        for row_idx in range(len(contracts)):
            tableWidget.setItem(row_idx, 0, QTableWidgetItem(str(contracts[row_idx])))
            pass

        header = tableWidget.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
            pass
        header.setStretchLastSection(True)

        
        # Stretch the headers horizontally
        tableWidget.horizontalHeader().setStretchLastSection(True)
        tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        return tableWidget
    
    def create_button(self, row, column, text=None, table=None, layout=None,image_path=None):
        '''
        Create button for a desired layout or table.
        
        Parameters:
        -----------
        row : int
            Row index for placement.
        column : int
            Column index for placement.
        text : str, optional
            Button text label.
        table : QTableWidget, optional
            Table to insert the button into.
        layout : QLayout, optional
            Layout to insert the button into.
        image_path : str, optional
            Path to an icon image for the button.
        
        Returns:
        ----------
        button
            The created button widget
        '''
        # https://doc.qt.io/archives/qtforpython-5/PySide2/QtGui/QIcon.html
        # https://www.pythonguis.com/faq/built-in-qicons-pyqt/
        
        # Default will be text, but if a path is given, we will use an image as the icon
        button = QPushButton()
        if image_path:
            button.setIcon(QIcon(image_path))
            pass
        if text:
            button.setText(text)
            pass

        if table:
            table.setCellWidget(row, column, button)
            pass
        else:
            layout.addWidget(button,row, column,alignment=Qt.AlignRight)
        return button

    def create_combobox(self, items, layout, row, column,width):
        '''
        Create a combination box for a desired layout.
        
        Parameters:
        -----------
        items : list[str]
            Items to populate the dropdown.
        layout : QLayout
            Layout to which the combobox is added.
        row : int
            Row position in the layout.
        column : int
            Column position in the layout.
        width : int
            Fixed width of the combobox.
        
        Returns:
        ----------
        combo_box
            The created combination box widget
        '''
        combo_box = QComboBox()
        combo_box.addItems(items)
        combo_box.setEditable(True)
        combo_box.lineEdit().setAlignment(Qt.AlignLeft)
        combo_box.setEditable(False)
        combo_box.setFixedWidth(width)

        layout.addWidget(combo_box, row, column)
        
        return combo_box

    def create_doublespinbox(self): #section, layout, location, row, column):
        '''
        Create and return a configured QSpinBox for selecting a confidence interval.

        The spin box allows the user to select a percentage value between 0 and 95,
        with increments of 5. The default value is set to 95 and a "%" suffix is
        displayed to indicate that the value represents a percentage.

        
        Returns
        -------
        QSpinBox
            A configured spin box widget for selecting a confidence interval.
        '''
        userinput = QSpinBox()
        userinput.setRange(0,95)
        userinput.setSingleStep(5)
        userinput.setValue(95)
        userinput.setSuffix("%")
        userinput.setFixedWidth(60)
    
        return userinput

    
    # ----------------------------------------------------------------
    # CALCULATIONS
    # ----------------------------------------------------------------
    def calc_conf_interval(self, z, p_hat, n_samples):
        '''
        Compute a binomial proportion confidence interval using the
        normal approximation (Wald interval).

        The interval is calculated as:
            phat +- z * sqrt(phat(1 − phat)/n)

        Parameters
        ----------
        z : float
            Z-score corresponding to the desired confidence level.

        p_hat : float
            Estimated proportion of successes (between 0 and 1).

        n_samples : int
            Number of samples used to estimate the proportion.

        Returns
        -------
        list[float]
            Lower and upper bounds of the confidence interval [lb, ub].
        '''
        lb = p_hat - z/((n_samples)**0.5) * (p_hat*(1 - p_hat))**0.5
        ub = p_hat + z/((n_samples)**0.5) * (p_hat*(1 - p_hat))**0.5

        confidence_interval = [lb, ub]
        return confidence_interval

    def calc_z(self, value):
        '''
        Convert a confidence level (percentage) to the corresponding
        standard normal Z-score.

        Parameters
        ----------
        value : float
           Desired confidence level expressed as a percentage
           (i.e. 95 for a 95% confidence interval).

        Returns
        -------
        float
            Z-score corresponding to the two-sided confidence level.
        '''
        # The Wilson Confidence Interval method uses standard normal zscores for a desired confidence interval.
        # Because we only do confidence intervals every 5%, there are only 20 values and we just do a table lookup here
        z = 0
        match value:
            case 95:
                z = 1.96
            case 90:
                z = 1.645
            case 85:
                z = 1.4395
            case 80:
                z = 1.2816
            case 75:
                z = 1.1503
            case 70:
                z = 1.0364
            case 65:
                z = 0.9346
            case 60:
                z = 0.8416
            case 55:
                z = 0.7554
            case 50:
                z = 0.6745
            case 45:
                z = 0.5978
            case 40:
                z = 0.5244
            case 35:
                z = 0.4538
            case 30:
                z = 0.3853
            case 25:
                z = 0.3186
            case 20:
                z = 0.2533
            case 15:
                z = 0.1891
            case 10:
                z = 0.1257
            case 5:
                z = 0.0627
            case _:
                z = 0
                print("Invalid confidence interval value")
            # p = 1 - (1 - value/100)/2 #p is also the mean for this distribution type
            # deviation = np.sqrt(p*(1-p)/n)
            # z = 1-((value/100) - p) / deviation
            # #z = np.sqrt(2)*erfinv(2*p - 1)
            # #z = 0
            # print("value: ", value)
            # print("deviation: ", deviation)
            # print("p: ", p)
            # print("z: ", z)
        return z


    def update_confidence_interval(self,value,table):
        '''
        Update the confidence interval column of the contract table when the
        confidence level changes in the QSpinBox.

        The function recalculates Wilson confidence intervals for each
        contract using the current success proportions and sample sizes,
        then updates the third column of the provided QTableWidget.

        Parameters
        ----------
        value : float
            Confidence level percentage selected by the user.

        table : QTableWidget
            Table widget whose confidence interval column should be updated.
        '''
        z = self.calc_z(value)
        for row_idx, (contract,n) in enumerate(self.current_num_samples_dict.items()):
            n = self.current_num_samples_dict[contract]
            p_hat = self.current_p_hat_dict[contract]
            lb, ub = self.calc_wilson_interval(z, p_hat, n)
            table.setItem(row_idx, 2, QTableWidgetItem(f"{lb*100:.2f}%, {ub*100:.2f}%"))
            pass
        return
        
    def calc_wilson_interval(self, z, p_hat, n_samples):
        '''
        Compute the Wilson score confidence interval for a binomial proportion.

        The Wilson interval provides a more reliable confidence interval for
        binomial proportions than the standard normal approximation, especially
        for small sample sizes or proportions near 0 or 1. We are unable to use
        the Wald Interval calculation, because as the confidence bounds
        approach 100%, we do not get good data. 

        Parameters 
        ----------
        z : float
            Z-score corresponding to the desired confidence level.

        p_hat : float
            Estimated proportion of successes (between 0 and 1).

        n_samples : int
            Number of observations used to estimate the proportion.

        Returns
        -------
        list[float]
            Lower and upper bounds of the Wilson confidence interval [lb, ub].
        '''
        # https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval#The_interval_equality_principle

        # Ensure samples are present:
        if n_samples == 0:
            return [0,0]
        denominator = 1 + z**2/n_samples
        center = (p_hat + z**2/(2*n_samples))/denominator
        margin = (z/denominator)*((p_hat*(1 - p_hat) + z**2/(4*n_samples))/n_samples)**0.5

        lb = center - margin
        ub = center + margin
        
        confidence_interval = [lb, ub]
        
        return confidence_interval 

    def calc_proportion(self, data_dict):
        '''
        Calculate success proportions and sample counts for each contract.

        The function iterates through iteration results for each contract
        and determines the proportion (phat) of successful evaluations
        along with the total number of samples.

        A successful event is defined through a true boolean. 

        Parameters
        ----------
        data_dict : dict[str, list[tuple[str, str]]]
            Dictionary mapping contract names to lists of evaluation tuples.
            Each tuple contains (time_value, boolean_value)

        Returns
        -------
        p_hat_dict : dict
            Dictionary mapping each contract to its estimated success
            proportion (p̂).

        n_dict : dict
            Dictionary mapping each contract to the total number of
            evaluations (sample size).
        '''
        # Returns a dictionary of the phat values per contract
        p_hat_dict = {}
        n_dict = {}
        for contract, data in data_dict.items():
            num_pass = 0
            n = 0
            for time_val, bool_val in data:
                n += 1
                if bool_val == "true":
                    num_pass += 1
                    pass
                pass
            if n == 0:
                p_hat_dict[contract] = 0
                pass
            else:
                p_hat_dict[contract] = num_pass/n
                pass
            
            n_dict[contract] = n
            pass
        return p_hat_dict, n_dict

    def calc_times(self, data_dict):
        '''
        Separate evaluation timestamps into passed and failed events.

        For each contract, this function scans evaluation results and records
        the timestamps at which the contract passed ("true") or failed ("false").

        Parameters
        ----------
        data_dict : dict[str, list[tuple[str, str]]]
            Dictionary mapping contract names to lists of evaluation tuples
            in the form (time_value, boolean_value).

        Returns
        -------
        failed_times : dict
            Dictionary mapping each contract to a list of timestamps where
            the evaluation result was "false".

        passed_times : dict
            Dictionary mapping each contract to a list of timestamps where
            the evaluation result was "true".
        '''
        # Determine the failed times per contract
        failed_times = {}
        passed_times = {}
        for contract, data in data_dict.items():
            failed_times[contract] = []
            passed_times[contract] = []
            for time_val, bool_val in data:
                if bool_val == "false":
                    failed_times[contract].append(time_val)
                    pass
                elif bool_val == "true":
                    passed_times[contract].append(time_val)
                    pass
                pass
            pass
        return failed_times, passed_times

    
    # ----------------------------------------------------------------
    # HEATMAP FEATURES
    # ----------------------------------------------------------------
    def add_another_heatmap_to_window(self,name, another_window):
        '''
        Add a selected item to the heatmap view in another window.

        This function updates the list of selected items used to generate
        the heatmap in the provided window. If "All Selections" is chosen,
        the window switches to a mode where all available contracts are
        displayed. Otherwise, the selected item is added to the list of
        heatmap selections if it is not already present.
        
        Parameters
        ----------
        name : str
            Name of the item selected by the user. This typically corresponds
            to a contract or data key used to generate the heatmap.

        another_window : object
            The window instance responsible for displaying the heatmap.
            This object is expected to contain the attributes:
              - selected_items (list)
              - all_selections_mode (bool)
 
        
        Parameters:
        -----------
        
        '''
        if name == "Data Status Selection":
            return
        
        if name == "All Selections":
            another_window.all_selections_mode = True
            another_window.selected_items = list(self.data_dict.keys())
            return
        else:
            another_window.all_selections_mode = False
        
            if name not in another_window.selected_items:
                another_window.selected_items.append(name)
                pass
            pass
        self.redraw_heatmap(another_window)
        return

    def redraw_heatmap(self, another_window):
        '''
        Regenerate and display the heatmap in the specified window.

        This function removes any existing heatmap canvas from the window,
        prepares the appropriate dataset based on the current selections,
        generates a new heatmap figure, and embeds it into the window.

        Parameters
        ----------
        another_window : QWidget
            The window instance that contains the heatmap display. This object
            is expected to have the following attributes:
              - selected_items (list): list of selected contracts or UUIDs
              - all_selections_mode (bool): whether all contracts should be shown
              - data_dict (dict): dictionary mapping contracts to evaluation data
              - heatmap_layout (QGridLayout): layout where the heatmap canvas
                is placed
        '''
        if hasattr(another_window, "canvas"):
            another_window.heatmap_layout.removeWidget(another_window.canvas)
            another_window.canvas.setParent(None)
            pass

        if another_window.all_selections_mode:
            contracts = list(another_window.data_dict.keys())
            data_to_use = another_window.data_dict

            pass
        else:
            contracts = another_window.selected_items
            data_to_use = {}
            for sel in contracts:
                if sel in self.data_dict:  # normal contract
                    data_to_use[sel] = self.data_dict[sel]
                    pass
                elif sel in self.uuid_dict:  # UUID
                    combined_data = []
                    for contract in self.uuid_dict[sel]:
                        combined_data += self.data_dict[contract]
                        pass
                    data_to_use[sel] = combined_data
                    pass
                pass
            pass

        fig = self.create_heatmap(
            selections=contracts,
            value_labels=True,
            data_dict=data_to_use
            )

        canvas = FigureCanvas(fig)
        another_window.canvas = canvas
        another_window.heatmap_layout.addWidget(canvas)
        return

    def open_another_window(self, data_dict, contract_name=None, all_selections=False):
        '''
        Create and display a new window containing a heatmap visualization.

        This function initializes a new window used to display heatmap
        visualizations for selected contracts or groups of contracts. It
        configures the layout, prepares the data for the heatmap, and
        attaches UI controls for dynamically adding additional selections.

        Parameters
        ----------
        data_dict : dict
            Dictionary mapping contract names to evaluation data. If None,
            the function uses `self.current_data_dict`.

        contract_name : str, optional
            Name of the contract to initially display in the heatmap.
            Ignored if `all_selections` is True.

        all_selections : bool, optional
            If True, the heatmap will display all available contracts
            from the current dataset.
        '''
        if data_dict is None:
            data_dict = self.current_data_dict
            pass
        
        if all_selections: # all selections case
            selected_items = list(self.current_data_dict.keys())
            all_selections_mode = True
            window_title = "All Selections"
            pass
        
        else: 
            selected_items = [contract_name]
            all_selections_mode = False
            window_title = contract_name
            pass
        
        another_window = AnotherWindow(window_title,self)
        another_window.selected_items = selected_items
        another_window.all_selections_mode = all_selections_mode
        another_window.heatmap_container = QWidget()
        another_window.heatmap_layout = QGridLayout(another_window.heatmap_container)
        another_window.another_layout.addWidget(another_window.heatmap_container, 1, 0, 1, -1)
        another_window.data_dict = {c: data_dict[c] for c in selected_items if c in data_dict}
        
        
        self.redraw_heatmap(another_window)
        #another_window.next_row += 1
        
        items = ["Data Status Selection"] + list(self.data_dict.keys()) + list(self.uuid_dict.keys()) + ["All Selections"]
        combo_box = self.create_combobox(items, another_window.another_layout,0,0,300)   
        combo_box.currentTextChanged.connect(
            lambda name: self.add_another_heatmap_to_window(name, another_window)
        )
        
                                                            
        another_window.show()

        if not hasattr(self, "open_windows"):
            self.open_windows = []
            pass
        self.open_windows.append(another_window)
        return
    
    def create_heatmap(self, selections, value_labels=True,data_dict=None):
        '''
        Generate a Matplotlib heatmap figure for selected contracts or UUIDs.

        The heatmap displays distance metric values over time.
        Values are averaged when multiple events occur at the same timestamp.

        Parameters:
        -----------
        selections : list[str]
            Contracts or UUIDs to visualize.
        value_labels : bool, optional
            Whether to overlay numeric values on the heatmap.
        data_dict : dict, optional
            Pre-filtered distance metric dataset. If None, the
            current execution dataset is used.

        Returns:
        -----------
        matplotlib.figure.Figure (fig)
            The generated heatmap figure.
        
        Resources:
        - https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
        - https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.imshow.html#matplotlib.axes.Axes.imshow
        '''
        # Need to make a heatmap where each data point is either pass or fail
        # i.e. pass = 100 percent, fail = 0%
        # failed_times is failed events
        # passed_times is passed events
        # -------------------------------
        # |        |   TIME 
        # -------------------------------
        # Contract | 0 | 1 | 2 | 3 | 4 | ... 
        # -------------------------------
        # | SPEC0  | 1 | 0 | 1 | 0 | 0 | ...
        # | SPEC1  | 0 | 1 | 1 | 0 | 1 | ...
        # | SPEC2  | 1 | 0 | 1 | 0 | 0 | ...
        # We want to have a "stream viewer" similarly to the waveform viewer
        if data_dict is None:
            data_dict = self.data_dict
            pass
        # Set title
        if len(selections) == len(self.data_dict):
            title = "All Selections Status"
            pass
        else:
            title = "Selected Status"
            pass
        # Determine max time across all selections
        max_time = 0
        for item in selections:
            if item in data_dict:
                events = data_dict[item]
                if events:
                    max_time = max(max_time, max(int(t) for t, _ in events))
                    pass
                pass
            elif item in self.uuid_dict:
                for contract in self.uuid_dict[item]:
                    events = self.data_dict.get(contract, [])
                    if events:
                        max_time = max(max_time, max(int(t) for t, _ in events))
                        pass
                    pass
                pass
            pass
        
        num_times = max_time + 1  # time starts at 0

        # Initialize heatmap array
        data_array = np.full((len(selections), num_times), np.nan)

        # Fill the array with pass/fail values
        for row_idx, item in enumerate(selections):
            # Case 1: data_dict already has the item (UUID pre-aggregated or normal contract)
            if item in data_dict:
                row_dict = {}
                for t, val in data_dict[item]:
                    col_idx = int(t)
                    if val == "true":
                        bool_val = 1
                        pass
                    elif val == "false":
                        bool_val = 0
                        pass
                    if col_idx not in row_dict:
                        row_dict[col_idx] = []
                        pass
                    row_dict[col_idx].append(bool_val)
                    pass
                row_array = np.full(num_times, np.nan)
                for col_idx, vals in row_dict.items():
                    row_array[col_idx] = np.mean(vals)
                    pass
                data_array[row_idx, :] = row_array
                continue

            # Case 2: item is a UUID, needs to combine underlying contracts
            elif item in self.uuid_dict:
                contracts_in_uuid = self.uuid_dict[item]
                temp_array = np.full((len(contracts_in_uuid), num_times), np.nan)
                for c_idx, contract in enumerate(contracts_in_uuid):
                    contract_events = self.data_dict.get(contract, [])
                    for t, val in contract_events:
                        col_idx = int(t)
                        temp_array[c_idx, col_idx] = 1 if val == "true" else 0
                        pass
                    pass
                
                if np.any(~np.isnan(temp_array)):
                    data_array[row_idx, :] = np.nanmean(temp_array, axis=0)
                    pass
                else:
                    print(f"Warning: UUID '{item}' has no valid data.")
                    pass
                pass
            else:
                print(f"Warning: '{item}' not found in data_dict or uuid_dict")
                continue
            pass

        base_height = 1.2
        fig_height = max(4, base_height * len(selections))
        fig,ax = plt.subplots(figsize=(8, fig_height))
        cmap = plt.get_cmap('RdYlGn')
        cmap.set_bad(color='lightgray')
        im = ax.imshow(data_array,cmap)

        ax.set_title(title)
        ax.set_xlabel("Time")
        ax.set_ylabel("Selection")

        # tick marks for y axis contracts and x axis events
        ax.set_yticks(np.arange(len(selections)))
        ax.set_yticklabels(selections)
        ax.set_xticks(np.arange(num_times))
        ax.set_xticklabels(np.arange(num_times))

        # Add grid lines
        ax.set_xticks(np.arange(-0.5, num_times, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(selections),1), minor=True)
        ax.grid(which='minor', color='w', linestyle='-', linewidth=1)
        ax.tick_params(which='minor', length=0) # hide tick marks for grid
                      
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(["Fail", "Pass"])
        cbar.set_label("Pass / Fail")
    
        # Optionality to add percentages or values onto the heatmap
        if value_labels:
            if np.all(np.isnan(data_array)):
                vmin = 0
                vmax = 1
                pass
            else:
                vmin = np.nanmin(data_array)
                vmax = np.nanmax(data_array)
                pass
            for i in range(data_array.shape[0]):
                for j in range(data_array.shape[1]):
                    value = data_array[i,j]
                    if not np.isnan(value): # skip nan vals
                        if vmax != vmin:
                            threshold = (vmax + vmin)/2
                            pass
                        else:
                            threshold = vmax/2
                            pass
                        text_color = "white" if value < threshold else "black"
                        ax.text(j,i,
                                f"{value:.2f}",
                                ha = "center",
                                va = "center",
                                color = text_color,
                                fontsize=8)
                        pass
                    pass
                pass
            pass
        
        
        return fig

    def build_left_column(self):
        # -------------------------------------------------------
        # LEFT COLUMN
        # -------------------------------------------------------
        # -------------- Contract Success ---------
        cs_section = QGroupBox("Contract Success")
        cs_layout = QGridLayout(cs_section)

        # ------- SETUP USER INPUT FOR CONF INTERVAL ----------
        conf_widget = QWidget()
        conf_layout = QHBoxLayout(conf_widget)
        conf_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel("Confidence Interval: ")

        conf_bound_input = self.create_doublespinbox()
        conf_layout.addWidget(label)
        conf_layout.addWidget(conf_bound_input)
        conf_layout.addStretch()

        cs_layout.addWidget(conf_widget)
        
        self.cs_table = self.create_table(
            ["SELECTION", "% PASSED", "CONFIDENCE INTERVAL"],
            len(self.contracts_dict), # we will have a row per contract
            self.contracts_dict,
            self.data_dict
            
        )
    
        
        # Assign the percent passed per contract row:
        for row_idx, contract in enumerate(self.p_hat_dict):
            percent = self.p_hat_dict[contract]*100
            self.cs_table.setItem(row_idx, 1, QTableWidgetItem(f"{percent:.2f}%"))
            pass

        # Confidence interval calculations:
        self.update_confidence_interval(95,self.cs_table) # default value is 95%

        conf_bound_input.valueChanged.connect(lambda value: self.update_confidence_interval(value, self.cs_table))
        
        cs_layout.addWidget(self.cs_table)
        self.left_col.addWidget(cs_section,0,0)

        # ---------- FAILED CONTRACT TIMES ---------
        fail_t_section = QGroupBox("Failed Times")
        fail_t_layout = QGridLayout(fail_t_section)
        self.fail_t_table = self.create_table(
            ["SELECTION", "FAILED TIMES"],
            len(self.contracts_dict),
            self.contracts_dict,
            self.data_dict
        )

        # Assign the failed times per contract row:
        for row_idx, contract in enumerate(self.failed_times_dict):
            unique_times = sorted(set(self.failed_times_dict[contract]),key=int)
            time_str = ", ".join(unique_times)
            self.fail_t_table.setItem(row_idx, 1, QTableWidgetItem(time_str))
            pass
        
        fail_t_layout.addWidget(self.fail_t_table)
        self.left_col.addWidget(fail_t_section,2,0)
        pass
    
    def build_right_column(self):
        # -------------------------------------------------------
        # RIGHT COLUMN
        # -------------------------------------------------------
        # -------------- Contract Status ---------
        cstat_section = QGroupBox("Selection Status")
        cstat_layout = QGridLayout(cstat_section)
        self.cstat_table = self.create_table(
            ["SELECTION", "STATUS"],
            len(self.contracts_dict),
            self.contracts_dict,
            self.data_dict
        )
        
        cstat_layout.addWidget(self.cstat_table)
        self.right_col.addWidget(cstat_section,0,1)

        for row_idx, contract_name in enumerate(self.contracts_dict):
            button = self.create_button(row_idx, 1, f"{contract_name} Data Status", self.cstat_table,None,None)
            button.clicked.connect(lambda checked=False, c=contract_name: self.open_another_window(data_dict=self.data_dict,contract_name=c))
            pass
        # ---- ALL CONTRACTS row ----
        all_row = len(self.contracts_dict)
        self.cstat_table.setRowCount(all_row + 1)
        
        self.cstat_table.setItem(all_row, 0, QTableWidgetItem("ALL SELECTIONS"))
        
        all_button = QPushButton("All Selections Status")
        self.cstat_table.setCellWidget(all_row, 1, all_button)
        all_button.clicked.connect(lambda checked=False: self.open_another_window(data_dict=self.data_dict,all_selections=True))

        
        pass         
    pass


def main():
    app = QApplication(sys.argv)
    # Trying to make this look more modern:
    app.setStyle("Fusion")
    '''
    app.setStyleSheet("""
    /* Base */
    QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: "Helvetica Neue";
    font-size: 14px;
    }
    
    /* Buttons */
    QPushButton {
    background-color: #1f6feb;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    }
    
    QPushButton:hover {
    background-color: #388bfd;
    }
    
    QPushButton:pressed {
    background-color: #1a5fd0;
    }
    
    /* Inputs */
    QLineEdit, QTextEdit, QComboBox {
    background-color: #1e1e1e;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #1f6feb;
    }
    
    /* Lists & tables */
    QListView, QTableView {
    background-color: #1e1e1e;
    border: none;
    }
    
    QHeaderView::section {
    background-color: #1a1a1a;
    padding: 6px;
    border: none;
    }
    
    /* Scrollbars */
    QScrollBar:vertical {
    background: transparent;
    width: 10px;
    }
    
    QScrollBar::handle:vertical {
    background: #333;
    border-radius: 5px;
    }
    
    QScrollBar::handle:vertical:hover {
    background: #444;
    }
    """)
    '''
    window = StreamViewer()
    window.show() # windows are automatically hidden, so this is required

    app.exec() # starts the event loop
    pass

if __name__ == "__main__":
    main()
