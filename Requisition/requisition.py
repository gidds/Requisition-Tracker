import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import csv

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
        window_width = int(screen_width * 0.6)
        window_height = int(screen_height * 0.6)
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
    def __init__(self, stock_items, master=None):
        super().__init__("New Requisition", master)
        self.stock_items = stock_items
        self.item_rows = []
        self.create_widgets()

    def create_widgets(self):
        self.scrollable_frame = self.create_scrollable_frame()

        requester_label = tk.Label(self.scrollable_frame, text="Who Requested the Items?")
        requester_label.pack()
        self.requester_entry = tk.Entry(self.scrollable_frame)
        self.requester_entry.pack()

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
            "Requester": requester,
            "Date": request_date,
            "Status": "Pending",
            "Items": items
        }
        save_to_xml(requisition)

        messagebox.showinfo("Success", "Requisition logged successfully!")
        self.root.destroy()

class MainMenu(BaseWindow):
    def __init__(self, stock_items):
        super().__init__("Requisition and Stock Management")
        self.stock_items = stock_items
        self.requisitions = self.load_requisitions()
        self.create_widgets()

    def create_widgets(self):
        new_requisition_button = tk.Button(self.frame, text="New Requisition", command=self.open_requisition)
        new_requisition_button.pack(pady=10)

        # Create a frame to hold the canvas and scrollbar
        self.canvas_frame = tk.Frame(self.frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create a canvas inside the frame
        self.canvas = tk.Canvas(self.canvas_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a scrollbar to the frame
        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Create a frame inside the canvas to hold the requisitions
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.display_requisitions()
    
    def display_requisitions(self):
        # Clear previous content
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        for req in self.requisitions:
            self.draw_requisition(req)

        # Update scroll region
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def draw_requisition(self, req):
        frame = tk.Frame(self.inner_frame, relief=tk.RIDGE, borderwidth=1)
        frame.pack(fill=tk.X, padx=5, pady=5, expand=True)

        header_frame = tk.Frame(frame)
        header_frame.pack(fill=tk.X)

        requester_label = tk.Label(header_frame, text=req['Requester'], anchor="w")
        requester_label.pack(side=tk.LEFT, padx=5)

        status_color = "red" if req['Status'] == 'Pending' else "green"
        status_label = tk.Label(header_frame, text=req['Status'], fg=status_color)
        status_label.pack(side=tk.RIGHT, padx=5)
        status_label.bind('<Button-1>', lambda e, r=req: self.toggle_status(r))

        items_frame = tk.Frame(frame)
        items_frame.pack(fill=tk.X)

        tk.Label(items_frame, text="Item", width=30, anchor="w").grid(row=0, column=0, padx=5)
        tk.Label(items_frame, text="Qty", width=10, anchor="w").grid(row=0, column=1, padx=5)

        for i, (item, qty) in enumerate(req['Items'], start=1):
            tk.Label(items_frame, text=item, anchor="w").grid(row=i, column=0, padx=5, sticky="w")
            tk.Label(items_frame, text=qty, anchor="w").grid(row=i, column=1, padx=5, sticky="w")

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
    
    def refresh_requisitions(self):
        self.requisitions = self.load_requisitions()
        self.display_requisitions()

    def open_requisition(self):
        self.root.withdraw()  # Hide the main window
        req_window = RequisitionWindow(self.stock_items, self.root)
        self.root.wait_window(req_window.root)
        self.root.deiconify()  # Show the main window again
        self.refresh_requisitions()

    def load_requisitions(self, filename='log_data.xml'):
        requisitions = []
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, filename)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            for req in root.findall('requisition'):
                requisition = {
                    'Requester': req.find('Requester').text,
                    'Date': req.find('Date').text,
                    'Status': req.find('Status').text,
                    'Items': [(item.find('Name').text, item.find('Quantity').text) for item in req.find('Items')]
                }
                requisitions.append(requisition)
            print(f"Loaded {len(requisitions)} requisitions")
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
    try:
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            for row in reader:
                stock_items.append(row[0])  # Assuming stock names are in the first column
    except IOError as e:
        print(f"Error loading stock items: {e}")
    return stock_items

def save_to_xml(requisition, filename='log_data.xml'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except (FileNotFoundError, ET.ParseError):
        root = ET.Element("requisitions")
        tree = ET.ElementTree(root)

    req_elem = ET.SubElement(root, "requisition")
    ET.SubElement(req_elem, "Requester").text = requisition["Requester"]
    ET.SubElement(req_elem, "Date").text = requisition["Date"]
    ET.SubElement(req_elem, "Status").text = requisition["Status"]
    
    items_elem = ET.SubElement(req_elem, "Items")
    for item, quantity in requisition["Items"]:
        item_elem = ET.SubElement(items_elem, "Item")
        ET.SubElement(item_elem, "Name").text = item
        ET.SubElement(item_elem, "Quantity").text = quantity

    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    print(f"Requisition saved to {file_path}")

def update_xml_status(completed_req, filename='log_data.xml'):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    for req in root.findall('requisition'):
        if (req.find('Requester').text == completed_req['Requester'] and
            req.find('Date').text == completed_req['Date']):
            req.find('Status').text = 'Completed'
            break

    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    print(f"Requisition status updated in {file_path}")

if __name__ == "__main__":
    stock_items = load_stock_items()
    main_menu = MainMenu(stock_items)
    main_menu.run()
