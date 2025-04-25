import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import customtkinter as ctk
import io
from PIL import Image, ImageTk
import os
import tkinter as tk
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import squarify
from wordcloud import WordCloud

class DataVisualization:
    """
    Utility class for creating data visualizations and embedding them in CustomTkinter frames
    """
    
    @staticmethod
    def create_bar_chart(data, x_column, y_column, title, xlabel, ylabel, frame, figsize=(8, 4)):
        """
        Create a bar chart and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - x_column: Column name for X-axis
        - y_column: Column name for Y-axis
        - title: Chart title
        - xlabel: X-axis label
        - ylabel: Y-axis label
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        data.plot(kind='bar', x=x_column, y=y_column, ax=ax, color='#3B8ED0')
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_line_chart(data, x_column, y_column, title, xlabel, ylabel, frame, figsize=(8, 4)):
        """
        Create a line chart and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - x_column: Column name for X-axis
        - y_column: Column name for Y-axis
        - title: Chart title
        - xlabel: X-axis label
        - ylabel: Y-axis label
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        data.plot(kind='line', x=x_column, y=y_column, ax=ax, color='#3B8ED0', marker='o')
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_pie_chart(data, labels, values, title, frame, figsize=(6, 6)):
        """
        Create a pie chart and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - labels: Column name for pie slice labels
        - values: Column name for pie slice values
        - title: Chart title
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        pie_labels = data[labels].tolist()
        pie_values = data[values].tolist()
        
        ax.pie(pie_values, labels=pie_labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        
        ax.set_title(title)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_scatter_plot(data, x_column, y_column, title, xlabel, ylabel, frame, color_column=None, figsize=(8, 4)):
        """
        Create a scatter plot and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - x_column: Column name for X-axis
        - y_column: Column name for Y-axis
        - title: Chart title
        - xlabel: X-axis label
        - ylabel: Y-axis label
        - frame: CustomTkinter frame to embed the chart
        - color_column: Column name for point colors (optional)
        - figsize: Figure size (width, height) in inches
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        if color_column:
            scatter = ax.scatter(data[x_column], data[y_column], c=data[color_column], cmap='viridis', alpha=0.7)
            plt.colorbar(scatter, ax=ax, label=color_column)
        else:
            ax.scatter(data[x_column], data[y_column], color='#3B8ED0', alpha=0.7)
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_heatmap(data, x_column, y_column, value_column, title, xlabel, ylabel, frame, figsize=(8, 6)):
        """
        Create a heatmap and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - x_column: Column name for X-axis
        - y_column: Column name for Y-axis
        - value_column: Column name for cell values
        - title: Chart title
        - xlabel: X-axis label
        - ylabel: Y-axis label
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        pivot_data = data.pivot_table(index=y_column, columns=x_column, values=value_column, aggfunc='mean')
        
        fig, ax = plt.subplots(figsize=figsize)
        
        colors = ['#3B8ED0', 'white', '#E74C3C']  
        cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=100)
        
        heatmap = ax.imshow(pivot_data, cmap=cmap, aspect='auto')
        
        cbar = plt.colorbar(heatmap, ax=ax)
        cbar.set_label(value_column)
        
        ax.set_title(title)
        
        ax.set_xticks(np.arange(len(pivot_data.columns)))
        ax.set_yticks(np.arange(len(pivot_data.index)))
        ax.set_xticklabels(pivot_data.columns)
        ax.set_yticklabels(pivot_data.index)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_wordcloud(text_data, title, frame, figsize=(8, 5), background_color='white'):
        """
        Create a word cloud visualization and embed it in a CustomTkinter frame
        
        Parameters:
        - text_data: Text content to create word cloud from (string, list of strings, or DataFrame column)
        - title: Chart title
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        - background_color: Background color for the word cloud
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        if isinstance(text_data, pd.Series):
            text = ' '.join(text_data.astype(str).tolist())
        elif isinstance(text_data, list):
            text = ' '.join([str(item) for item in text_data])
        else:
            text = str(text_data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        wordcloud = WordCloud(
            background_color=background_color,
            width=800,
            height=500,
            max_words=150,
            colormap='viridis',
            contour_width=1,
            contour_color='#3B8ED0'
        ).generate(text)
        
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        ax.set_title(title)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_treemap(data, labels_column, values_column, title, frame, figsize=(8, 6), cmap='viridis'):
        """
        Create a treemap visualization and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - labels_column: Column name for box labels
        - values_column: Column name for box sizes
        - title: Chart title
        - frame: CustomTkinter frame to embed the chart
        - figsize: Figure size (width, height) in inches
        - cmap: Colormap for the treemap
        
        Returns:
        - FigureCanvasTkAgg object
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        fig, ax = plt.subplots(figsize=figsize)
        
        labels = data[labels_column].tolist()
        sizes = data[values_column].tolist()
        
        normalized_sizes = (data[values_column] - data[values_column].min()) / (data[values_column].max() - data[values_column].min())
        colors = plt.cm.get_cmap(cmap)(normalized_sizes)
        
        squarify.plot(sizes=sizes, label=labels, alpha=0.8, color=colors, ax=ax, text_kwargs={'fontsize':12})
        
        ax.axis('off')
        
        ax.set_title(title, fontsize=14)
        
        sm = plt.cm.ScalarMappable(cmap=plt.cm.get_cmap(cmap))
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax)
        cbar.set_label(values_column)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
        return canvas
    
    @staticmethod
    def create_data_table(data, frame, max_rows=0):
        """
        Create a data table and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - frame: CustomTkinter frame to embed the table
        - max_rows: Maximum number of rows to display (0 for all rows)
        
        Returns:
        - None
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        if max_rows > 0 and len(data) > max_rows:
            display_data = data.head(max_rows)
            limited = True
        else:
            display_data = data
            limited = False
        
        columns = data.columns.tolist()
        rows = display_data.values.tolist()
        
        container_frame = ctk.CTkFrame(frame)
        container_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        canvas = tk.Canvas(container_frame, highlightthickness=0)
        
        y_scrollbar = ctk.CTkScrollbar(container_frame, orientation="vertical", command=canvas.yview)
        
        x_scrollbar = ctk.CTkScrollbar(container_frame, orientation="horizontal", command=canvas.xview)
        
        table_frame = ctk.CTkFrame(canvas)
        
        canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        canvas.pack(side="left", fill="both", expand=True)
        
        canvas_window = canvas.create_window((0, 0), window=table_frame, anchor="nw")
        
        column_widths = {}
        for i, col in enumerate(columns):
            width = max(len(col) * 10, 150)
            column_widths[i] = width
            
            header_label = ctk.CTkLabel(table_frame, text=col, font=ctk.CTkFont(weight="bold"), width=width)
            header_label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for i, row_data in enumerate(rows):
            for j, cell_data in enumerate(row_data):
                if isinstance(cell_data, (float, int)):
                    cell_text = f"{cell_data:,}"
                else:
                    cell_text = str(cell_data)
                
                content_width = min(len(cell_text) * 7, 500)
                column_widths[j] = max(column_widths[j], content_width)
                
                cell_label = ctk.CTkLabel(
                    table_frame, 
                    text=cell_text,
                    width=column_widths[j],
                    anchor="w",
                    wraplength=0
                )
                cell_label.grid(row=i+1, column=j, padx=5, pady=2, sticky="w")
        
        if limited:
            note_text = f"Showing {len(display_data)} of {len(data)} rows"
            note_label = ctk.CTkLabel(frame, text=note_text, font=ctk.CTkFont(size=10))
            note_label.pack(pady=5)
        else:
            count_text = f"Total rows: {len(data)}"
            count_label = ctk.CTkLabel(frame, text=count_text, font=ctk.CTkFont(size=10))
            count_label.pack(pady=5)
        
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            canvas.itemconfig(canvas_window, width=max(sum(column_widths.values()) + len(columns) * 10, canvas.winfo_width()))
        
        table_frame.bind("<Configure>", on_configure)
        
        def _on_vertical_scroll(event):
            if event.state & 0x4:
                canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            else:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        if os.name == 'posix':
            canvas.bind_all("<MouseWheel>", _on_vertical_scroll)
            canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        else:
            canvas.bind_all("<MouseWheel>", _on_vertical_scroll)
            
        table_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    @staticmethod
    def create_text_summary(data, summary_function, frame):
        """
        Create a text summary and embed it in a CustomTkinter frame
        
        Parameters:
        - data: DataFrame containing the data
        - summary_function: Function that takes a DataFrame and returns a summary string
        - frame: CustomTkinter frame to embed the summary
        
        Returns:
        - None
        """
        for widget in frame.winfo_children():
            widget.destroy()
        
        summary_text = summary_function(data)
        
        text_widget = ctk.CTkTextbox(frame, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget.insert("1.0", summary_text)
        text_widget.configure(state="disabled") 