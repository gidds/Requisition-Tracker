import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import csv
import sys
import chardet
import uuid

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class BaseWindow:
    def __init__(self, title, master=None):
        self.root = tk.Toplevel(master) if master else tk.Tk()
        self.setup_window(title)
        self.frame = tk.Frame(self.root)
        self.frame.pack(expand=True, fill=tk.BOTH)

    def setup_window(self, title):
        self.root.title(title)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def create_scrollable_frame(self):
        canvas = tk.Canvas(self.frame)
        scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame

    def run(self):
        self.root.mainloop()

class RequisitionWindow(BaseWindow):
    def __init__(self, stock_items, departments, master=None):
        super().__init__("New Requisition", master)
        self.stock_items = stock_items
        self.departments = departments
        self.item_rows = []
        self.create_widgets()

    def create_widgets(self):
        self.scrollable_frame = self.create_scrollable_frame()

        requester_label = tk.Label(self.scrollable_frame, text="Who Requested the Items?")
        requester_label.pack()
        self.requester_entry = tk.Entry(self.scrollable_frame)
        self.requester_entry.pack()

        department_label = tk.Label(self.scrollable_frame, text="Department")
        department_label.pack()
        self.department_var = tk.StringVar(self.root)
        self.department_var.set(self.departments[0])
        department_combobox = ttk.Combobox(self.scrollable_frame, textvariable=self.department_var, values=self.departments)
        department_combobox.pack()

        self.items_frame = tk.Frame(self.scrollable_frame)
        self.items_frame.pack(fill=tk.X, padx=10, pady=10)

        self.add_item_row()

        add_item_button = tk.Button(self.scrollable_frame, text="+", command=self.add_item_row)
        add_item_button.pack()

        button_frame = tk.Frame(self.scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        submit_button = tk.Button(button_frame, text="Submit", command=self.submit_requisition)
        submit_button.pack(side=tk.LEFT, padx=5)

        back_button = tk.Button(button_frame, text="Back", command=self.go_back)
        back_button.pack(side=tk.LEFT, padx=5)

    def go_back(self):
        self.root.destroy()

    def add_item_row(self):
        row_frame = tk.Frame(self.items_frame)
        row_frame.pack(fill=tk.X, pady=5)

        stock_var = tk.StringVar(self.root)
        stock_combobox = ttk.Combobox(row_frame, textvariable=stock_var, values=self.stock_items)
        stock_combobox.pack(side=tk.LEFT)

        quantity_entry = tk.Entry(row_frame, width=10)
        quantity_entry.pack(side=tk.LEFT, padx=5)

        remove_button = tk.Button(row_frame, text="-", command=lambda: self.remove_item_row(row_frame))
        remove_button.pack(side=tk.LEFT)

        stock_combobox.bind('<KeyRelease>', lambda event: self.update_combobox(event, stock_combobox))

        self.item_rows.append((stock_var, quantity_entry))

    def remove_item_row(self, row_frame):
        row_frame.destroy()
        self.item_rows = [(stock_var, quantity_entry) for stock_var, quantity_entry in self.item_rows
                          if stock_var.winfo_exists()]

    def update_combobox(self, event, combobox):
        current_text = combobox.get().lower()
        filtered_items = [item for item in self.stock_items + ["Other"] if current_text in item.lower()]
        combobox['values'] = filtered_items

    def submit_requisition(self):
        requester = self.requester_entry.get()
        request_date = datetime.now().strftime('%Y-%m-%d %H:%M')

        if not requester:
            messagebox.showwarning("Input Error", "Please enter the requester's name.")
            return

        items = []
        for stock_var, quantity_entry in self.item_rows:
            item = stock_var.get()
            quantity = quantity_entry.get()

            if item == "Other" or item not in self.stock_items:
                item = simpledialog.askstring("Custom Item", "Enter the item name:")

            if item and quantity:
                items.append((item, quantity))

        if not items:
            messagebox.showwarning("Input Error", "Please add at least one item to the requisition.")
            return

        requisition = {
            "ID": str(uuid.uuid4())[:8],
            "Requester": requester,
            "Date": request_date,
            "Status": "Pending",
            "Department": self.department_var.get(),
            "Items": items
        }
        if save_to_xml(requisition):
            messagebox.showinfo("Success", "Requisition logged successfully!")
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Failed to save requisition. Please try again.")

class MainMenu(BaseWindow):
    def __init__(self, stock_items):
        super().__init__("Requisition and Stock Management")
        self.stock_items = stock_items
        self.requisitions = self.load_requisitions()
        self.create_widgets()

    def load_departments(self, filename='Requisition/department.csv'):
        departments = []
        file_path = resource_path(filename)
        try:
            with open(file_path, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    departments.append(row[0])
        except FileNotFoundError:
            print(f"File not found: {file_path}")
    
        # Create a StringVar to hold the selected department
        self.department_var = tk.StringVar(self.root)
        self.department_var.trace("w", lambda *args: self.filter_departments())
    
        # Create the dropdown menu
        self.department_menu = tk.OptionMenu(self.root, self.department_var, *departments)
        self.department_menu.pack()
    
        return departments
    
    def filter_departments(self):
        selected_department = self.department_var.get()
        print(f"Selected department: {selected_department}")
    
        # Filter the list of departments based on the selected department
        filtered_departments = [department for department in self.departments if department.startswith(selected_department)]
    
        # Update the dropdown menu with the filtered list of departments
        self.department_menu['menu'].delete(0, 'end')
        for department in filtered_departments:
            self.department_menu['menu'].add_command(label=department, command=lambda value=department: self.department_var.set(value))

    def create_widgets(self):
        new_requisition_button = tk.Button(self.frame, text="New Requisition", command=self.open_requisition)
        new_requisition_button.pack(pady=10)

        # Create a frame to hold both scrollable areas
        self.requisitions_frame = tk.Frame(self.frame)
        self.requisitions_frame.pack(fill=tk.BOTH, expand=True)

        # Create pending requisitions frame
        self.pending_frame, self.pending_canvas, self.pending_inner = self.create_scrollable_area(self.requisitions_frame, "Pending Requisitions")
        self.pending_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create completed requisitions frame
        self.completed_frame, self.completed_canvas, self.completed_inner = self.create_scrollable_area(self.requisitions_frame, "Completed Requisitions")
        self.completed_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.display_requisitions()

    def create_scrollable_area(self, parent, title):
        frame = tk.LabelFrame(parent, text=title)
        
        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        
        inner_frame = tk.Frame(canvas)
        
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        return frame, canvas, inner_frame

    
    def display_requisitions(self):
        #print("Starting display_requisitions")
        # Clear previous content
        for widget in self.pending_inner.winfo_children():
            widget.destroy()
        for widget in self.completed_inner.winfo_children():
            widget.destroy()

        pending_count = 0
        completed_count = 0

        

        for req in self.requisitions:
            if req['Status'] == 'Pending':
                self.draw_requisition(req, self.pending_inner)
                pending_count += 1
            else:
                self.draw_requisition(req, self.completed_inner)
                completed_count += 1

        # Update scroll regions
        self.pending_inner.update_idletasks()
        self.pending_canvas.configure(scrollregion=self.pending_canvas.bbox("all"))
    
        self.completed_inner.update_idletasks()
        self.completed_canvas.configure(scrollregion=self.completed_canvas.bbox("all"))

        #print(f"Displayed {pending_count} pending and {completed_count} completed requisitions")


    def draw_requisition(self, req, parent_frame):
        #print(f"Drawing requisition: {req['Requester']} - {req['Status']}")
        frame = tk.Frame(parent_frame, relief=tk.RIDGE, borderwidth=1)
        frame.pack(fill=tk.X, padx=5, pady=5, expand=True)

        header_frame = tk.Frame(frame)
        header_frame.pack(fill=tk.X)

        id_requester_label = tk.Label(header_frame, text=f"{req['ID']} - {req['Requester']}", anchor="w")
        id_requester_label.pack(side=tk.LEFT, padx=5)

        status_color = "red" if req['Status'] == 'Pending' else "green"
        status_label = tk.Label(header_frame, text=req['Status'], fg=status_color)
        status_label.pack(side=tk.RIGHT, padx=5)
        status_label.bind('<Button-1>', lambda e, r=req: self.toggle_status(r))

    # Add date label for completed requisitions
        if req['Status'] == 'Completed':
            date_label = tk.Label(header_frame, text=req['Date'], anchor="e")
            date_label.pack(side=tk.RIGHT, padx=5)

        if req['Status'] == 'Completed':
            department_label = tk.Label(header_frame, text=req['Department'], anchor="e")
            department_label.pack(side=tk.RIGHT, padx=5)

    #Add date label for pending requisitions
        if req['Status'] == 'Pending':
            date_label = tk.Label(header_frame, text=req['Date'], anchor="e")
            date_label.pack(side=tk.RIGHT, padx=5)
    #Add Department label for pending requisitions
        if req['Status'] == 'Pending':
            department_label = tk.Label(header_frame, text=req['Department'], anchor="e")
            department_label.pack(side=tk.RIGHT, padx=5)

        items_frame = tk.Frame(frame)
        items_frame.pack(fill=tk.X)

        tk.Label(items_frame, text="Item", width=30, anchor="w").grid(row=0, column=0, padx=5)
        tk.Label(items_frame, text="Qty", width=10, anchor="w").grid(row=0, column=1, padx=5)

        for i, (item, qty) in enumerate(req['Items'], start=1):
            tk.Label(items_frame, text=item, anchor="w").grid(row=i, column=0, padx=5, sticky="w")
            tk.Label(items_frame, text=qty, anchor="w").grid(row=i, column=1, padx=5, sticky="w")

        #print(f"Finished drawing requisition: {req['Requester']}")

    
    def toggle_status(self, req):
        if req['Status'] == 'Pending':
            if messagebox.askyesno("Mark Complete", "Do you want to mark requisition {req['ID']} for {['Requester']} as complete?"):
                req['Status'] = 'Completed'
                update_xml_status(req)
                self.refresh_requisitions()
        else:
            if messagebox.askyesno("Mark Pending", "Do you want to mark requisition {req['ID']} for {['Requester']} as pending?"):
                req['Status'] = 'Pending'
                update_xml_status(req)
                self.refresh_requisitions()
    
    def refresh_requisitions(self):
        self.requisitions = self.load_requisitions()
        #print(f"Refreshed requisitions. Total count: {len(self.requisitions)}")
        self.display_requisitions()
        self.root.update()  # Force update of the main window

    def open_requisition(self):
        self.root.withdraw()  # Hide the main window
        departments = self.load_departments()
        if not departments:
                departments = ['Stores']
        req_window = RequisitionWindow(self.stock_items,departments, self.root)
        self.root.wait_window(req_window.root)
        self.root.deiconify()  # Show the main window again
        self.refresh_requisitions()

    def load_requisitions(self, filename='Requisition/log_data.xml'):
        requisitions = []
        file_path = resource_path(filename)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for req in root.findall('requisition'):
                requisition = {
                'ID': req.find('ID').text if req.find('ID') is not None else str(uuid.uuid4())[:8],
                'Requester': req.find('Requester').text,
                'Date': req.find('Date').text,
                'Status': req.find('Status').text,
                'Department': req.find('Department').text if req.find('Department') is not None else '',
                'Items': [(item.find('Name').text, item.find('Quantity').text) for item in req.find('Items')]
                }
                requisitions.append(requisition)
            print(f"Loaded {len(requisitions)} requisitions")
            for idx, req in enumerate(requisitions):
                print(f"Requisition {idx + 1}: {req['ID']} - {req['Requester']} - {req['Status']}")
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except ET.ParseError as e:
            print(f"Error parsing XML: {e}")
        return requisitions


    def toggle_status(self, req):
        if req['Status'] == 'Pending':
            if messagebox.askyesno("Mark Complete", "Do you want to mark this requisition as complete?"):
                req['Status'] = 'Completed'
                update_xml_status(req)
                self.refresh_requisitions()
        else:
            if messagebox.askyesno("Mark Pending", "Do you want to mark this requisition as pending?"):
                req['Status'] = 'Pending'
                update_xml_status(req)
                self.refresh_requisitions()
    
    def mark_complete(self, req):
        req['Status'] = 'Completed'
        update_xml_status(req)
        self.refresh_requisitions()

    def refresh_requisitions(self):
        self.requisitions = self.load_requisitions()
        self.display_requisitions()
        
    def run(self):
        self.root.after(100, self.refresh_requisitions)  # Refresh shortly after starting
        self.root.mainloop()

def load_stock_items(filename='stock_items.csv'):
    stock_items = []
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    #print(f"Attempting to load stock items from: {file_path}")

    # Detect the file encoding
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read()
        detected = chardet.detect(raw_data)
        encoding = detected['encoding']
        print(f"Detected encoding: {encoding}")
    except IOError as e:
        print(f"Error reading file for encoding detection: {e}")
        return stock_items

    # Try to read the file with the detected encoding
    try:
        with open(file_path, mode='r', encoding=encoding) as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header, use None to handle empty files
            for row in reader:
                if row:  # Check if the row is not empty
                    stock_items.append(row[0].strip())  # Assuming stock names are in the first column, strip whitespace
    except UnicodeDecodeError as e:
        print(f"Error with detected encoding: {e}. Trying with 'utf-8' and 'latin-1' encodings.")
        
        # If the detected encoding fails, try with 'utf-8' and then 'latin-1'
        for fallback_encoding in ['utf-8', 'latin-1']:
            try:
                with open(file_path, mode='r', encoding=fallback_encoding) as file:
                    reader = csv.reader(file)
                    next(reader, None)  # Skip header, use None to handle empty files
                    for row in reader:
                        if row:  # Check if the row is not empty
                            stock_items.append(row[0].strip())  # Assuming stock names are in the first column, strip whitespace
                print(f"Successfully read file with {fallback_encoding} encoding.")
                break  # Exit the loop if successful
            except UnicodeDecodeError:
                print(f"Failed to read with {fallback_encoding} encoding.")
    except IOError as e:
        print(f"Error loading stock items: {e}")

    #print(f"Loaded {len(stock_items)} stock items.")
    return stock_items


def save_to_xml(requisition, filename='Requisition/log_data.xml'):
    file_path = resource_path(filename)
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError):
        root = ET.Element("requisitions")
        tree = ET.ElementTree(root)

    req_elem = ET.SubElement(root, "requisition")
    ET.SubElement(req_elem, "ID").text = str(uuid.uuid4())[:8]  # Use first 8 characters of a UUID
    ET.SubElement(req_elem, "Requester").text = requisition["Requester"]
    ET.SubElement(req_elem, "Date").text = requisition["Date"]
    ET.SubElement(req_elem, "Status").text = requisition["Status"]
    ET.SubElement(req_elem, "Department").text = requisition["Department"]
    
    items_elem = ET.SubElement(req_elem, "Items")
    for item, quantity in requisition["Items"]:
        item_elem = ET.SubElement(items_elem, "Item")
        ET.SubElement(item_elem, "Name").text = item
        ET.SubElement(item_elem, "Quantity").text = quantity

    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    print(f"Requisition saved to {file_path}")
    
    try:
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        print(f"Requisition saved to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving requisition: {e}")
        return False

def update_xml_status(updated_req, filename='Requisition/log_data.xml'):
    file_path = resource_path(filename)
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    for req in root.findall('requisition'):
        # First, try to match by ID if it exists
        if 'ID' in updated_req and req.find('ID') is not None:
            if req.find('ID').text == updated_req['ID']:
                req.find('Status').text = updated_req['Status']
                break
        # If ID doesn't exist or doesn't match, fall back to the original method
        elif (req.find('Requester').text == updated_req['Requester'] and
              req.find('Date').text == updated_req['Date']):
            req.find('Status').text = updated_req['Status']
            break

    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    print(f"Requisition status updated to {updated_req['Status']} in {file_path}")

if __name__ == "__main__":
    stock_items = load_stock_items()
    main_menu = MainMenu(stock_items)
    main_menu.run()
