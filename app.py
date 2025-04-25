import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import praw
import requests
import webbrowser

from news_api import NewsAPIClient
from government_data import GovernmentDataClient
from flight_data import FlightDataClient
from data_visualization import DataVisualization
from reddit_api import RedditClient
import config

ctk.set_appearance_mode(config.APPEARANCE_MODE)
ctk.set_default_color_theme(config.THEME)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("OSINT Collector")
        self.geometry(config.WINDOW_SIZE)
        
        self.init_clients()
        
        self.tabview = ctk.CTkTabview(self, width=1160, height=760)
        self.tabview.pack(padx=20, pady=20)
        
        self.tab_news = self.tabview.add("News API")
        self.tab_reddit = self.tabview.add("Reddit")
        self.tab_government = self.tabview.add("Government Data")
        self.tab_flights = self.tabview.add("Flight Data")
        
        self.tabview.set("Flight Data")
        
        self.setup_news_tab()
        self.setup_reddit_tab()
        self.setup_government_tab()
        self.setup_flights_tab()
    
    def init_clients(self):
        try:
            self.news_client = NewsAPIClient(config.NEWSAPI_KEY)
        except Exception as e:
            print(f"Error initializing News API client: {e}")
            self.news_client = None
        
        try:
            self.reddit_client = RedditClient(
                config.REDDIT_CLIENT_ID,
                config.REDDIT_CLIENT_SECRET,
                config.REDDIT_USER_AGENT
            )
        except Exception as e:
            print(f"Error initializing Reddit client: {e}")
            self.reddit_client = None
        
        try:
            self.gov_client = GovernmentDataClient(config.GOVERNMENT_DATA_KEY)
        except Exception as e:
            print(f"Error initializing Government Data client: {e}")
            self.gov_client = None
        
        try:
            self.flight_client = FlightDataClient(config.AVIATIONSTACK_KEY)
        except Exception as e:
            print(f"Error initializing Flight Data client: {e}")
            self.flight_client = None
    
    def setup_news_tab(self):
        header = ctk.CTkLabel(self.tab_news, text="News API Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        control_frame = ctk.CTkFrame(self.tab_news)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        search_label = ctk.CTkLabel(control_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.news_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(control_frame, textvariable=self.news_search_var, width=200)
        search_entry.grid(row=0, column=1, padx=10, pady=10)
        
        self.news_title_only_var = ctk.BooleanVar(value=False)
        title_only_checkbox = ctk.CTkCheckBox(control_frame, text="Search in titles only", variable=self.news_title_only_var)
        title_only_checkbox.grid(row=0, column=2, padx=10, pady=10)
        
        category_label = ctk.CTkLabel(control_frame, text="Category:")
        category_label.grid(row=0, column=3, padx=10, pady=10)
        
        categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
        self.news_category_var = ctk.StringVar(value="")
        category_dropdown = ctk.CTkOptionMenu(control_frame, values=[""] + categories, variable=self.news_category_var)
        category_dropdown.grid(row=0, column=4, padx=10, pady=10)
        
        country_label = ctk.CTkLabel(control_frame, text="Country:")
        country_label.grid(row=0, column=5, padx=10, pady=10)
        
        countries = [
            ("us", "United States"),
            ("gb", "United Kingdom"),
            ("ca", "Canada"),
            ("au", "Australia"),
            ("in", "India"),
            ("", "All")
        ]
        self.news_country_var = ctk.StringVar(value="us")
        country_dropdown = ctk.CTkOptionMenu(
            control_frame,
            values=[code for code, name in countries],
            variable=self.news_country_var
        )
        country_dropdown.grid(row=0, column=6, padx=10, pady=10)
        
        from datetime import datetime, timedelta
        
        date_label = ctk.CTkLabel(control_frame, text="Date Range:")
        date_label.grid(row=1, column=0, padx=10, pady=10)
        
        self.news_days_back_var = ctk.IntVar(value=7)
        
        days_slider = ctk.CTkSlider(
            control_frame, 
            from_=1, 
            to=29, 
            number_of_steps=28,
            variable=self.news_days_back_var,
            command=self.update_date_range_label
        )
        days_slider.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.date_range_label = ctk.CTkLabel(control_frame, text="")
        self.date_range_label.grid(row=1, column=3, columnspan=2, padx=10, pady=10, sticky="w")
        
        self.update_date_range_label(self.news_days_back_var.get())
        
        search_button = ctk.CTkButton(control_frame, text="Search News", command=self.fetch_news)
        search_button.grid(row=1, column=6, padx=20, pady=10)
        
        self.news_content_frame = ctk.CTkFrame(self.tab_news)
        self.news_content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.news_tabview = ctk.CTkTabview(self.news_content_frame, width=1120, height=680)
        self.news_tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.news_overview_tab = self.news_tabview.add("Overview")
        self.news_wordcloud_tab = self.news_tabview.add("Word Cloud")
        self.news_treemap_tab = self.news_tabview.add("Source Treemap")
        
        self.news_tabview.set("Overview")
        
        self.news_top_frame = ctk.CTkFrame(self.news_overview_tab)
        self.news_top_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.news_table_frame = ctk.CTkFrame(self.news_top_frame)
        self.news_table_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.news_chart_frame = ctk.CTkFrame(self.news_top_frame)
        self.news_chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        placeholder = ctk.CTkLabel(self.news_table_frame, text="Search for news to see results")
        placeholder.pack(pady=50)
        
        chart_placeholder = ctk.CTkLabel(self.news_chart_frame, text="Source distribution will appear here")
        chart_placeholder.pack(pady=50)
        
        wordcloud_placeholder = ctk.CTkLabel(self.news_wordcloud_tab, text="Search for news to generate a word cloud")
        wordcloud_placeholder.pack(pady=50)
        
        treemap_placeholder = ctk.CTkLabel(self.news_treemap_tab, text="Search for news to see source distribution as treemap")
        treemap_placeholder.pack(pady=50)
    
    def update_date_range_label(self, value=None):
        from datetime import datetime, timedelta
        
        to_date = datetime.now().date()
        
        days_back = self.news_days_back_var.get()
        from_date = to_date - timedelta(days=days_back)
        
        from_date_str = from_date.strftime("%Y-%m-%d")
        to_date_str = to_date.strftime("%Y-%m-%d")
        
        self.date_range_label.configure(
            text=f"From {from_date_str} to {to_date_str} ({days_back} days)"
        )
    
    def setup_reddit_tab(self):
        header = ctk.CTkLabel(self.tab_reddit, text="Reddit Data Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        control_frame = ctk.CTkFrame(self.tab_reddit)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        search_label = ctk.CTkLabel(control_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.reddit_search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(control_frame, textvariable=self.reddit_search_var, width=200)
        search_entry.grid(row=0, column=1, padx=10, pady=10)
        
        subreddit_label = ctk.CTkLabel(control_frame, text="Subreddit:")
        subreddit_label.grid(row=0, column=2, padx=10, pady=10)
        
        self.reddit_subreddit_var = tk.StringVar()
        subreddit_entry = ctk.CTkEntry(control_frame, textvariable=self.reddit_subreddit_var, width=150)
        subreddit_entry.grid(row=0, column=3, padx=10, pady=10)
        
        sort_label = ctk.CTkLabel(control_frame, text="Sort:")
        sort_label.grid(row=0, column=4, padx=10, pady=10)
        
        sort_types = ["search"]
        self.reddit_sort_var = ctk.StringVar(value="search")
        sort_dropdown = ctk.CTkOptionMenu(control_frame, values=sort_types, variable=self.reddit_sort_var)
        sort_dropdown.grid(row=0, column=5, padx=10, pady=10)
        
        count_label = ctk.CTkLabel(control_frame, text="Count:")
        count_label.grid(row=0, column=6, padx=10, pady=10)
        
        self.reddit_count_var = ctk.IntVar(value=10)
        count_slider = ctk.CTkSlider(control_frame, from_=5, to=100, number_of_steps=19, variable=self.reddit_count_var)
        count_slider.grid(row=0, column=7, padx=10, pady=10)
        
        count_value = ctk.CTkLabel(control_frame, textvariable=self.reddit_count_var)
        count_value.grid(row=0, column=8, padx=5, pady=10)
        
        search_button = ctk.CTkButton(control_frame, text="Search Reddit", command=self.fetch_reddit)
        search_button.grid(row=0, column=9, padx=20, pady=10)
        
        self.reddit_content_frame = ctk.CTkFrame(self.tab_reddit)
        self.reddit_content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.reddit_left_frame = ctk.CTkFrame(self.reddit_content_frame)
        self.reddit_left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        self.reddit_right_frame = ctk.CTkFrame(self.reddit_content_frame)
        self.reddit_right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        placeholder = ctk.CTkLabel(self.reddit_left_frame, text="Search for posts to see results")
        placeholder.pack(pady=50)
        
        chart_placeholder = ctk.CTkLabel(self.reddit_right_frame, text="Post analytics will appear here")
        chart_placeholder.pack(pady=50)
    
    def setup_government_tab(self):
        header = ctk.CTkLabel(self.tab_government, text="Government Data Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        control_frame = ctk.CTkFrame(self.tab_government)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        source_label = ctk.CTkLabel(control_frame, text="Data Source:")
        source_label.grid(row=0, column=0, padx=10, pady=10)
        
        sources = [
            "FDA Food Recalls",
            "Census Population"
        ]
        self.gov_source_var = ctk.StringVar(value=sources[0])
        source_dropdown = ctk.CTkOptionMenu(control_frame, values=sources, variable=self.gov_source_var, command=self.update_gov_params)
        source_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
        self.gov_param_frame = ctk.CTkFrame(control_frame)
        self.gov_param_frame.grid(row=0, column=2, columnspan=4, padx=10, pady=10, sticky="w")
        
        fetch_button = ctk.CTkButton(control_frame, text="Fetch Data", command=self.fetch_government)
        fetch_button.grid(row=0, column=6, padx=20, pady=10)
        
        self.gov_content_frame = ctk.CTkFrame(self.tab_government)
        self.gov_content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        placeholder = ctk.CTkLabel(self.gov_content_frame, text="Select a data source and fetch data to see results")
        placeholder.pack(pady=50)
        
       
        self.update_gov_params(sources[0])
    
    def update_gov_params(self, source):
        for widget in self.gov_param_frame.winfo_children():
            widget.grid_forget()
        
        if source == "FDA Food Recalls":
            recall_limit_label = ctk.CTkLabel(self.gov_param_frame, text="Number of Recalls:")
            recall_limit_label.grid(row=0, column=0, padx=10, pady=10)
            
            if not hasattr(self, 'recall_limit_var'):
                self.recall_limit_var = ctk.IntVar(value=25)
            
            recall_limit_slider = ctk.CTkSlider(
                self.gov_param_frame, 
                from_=10, 
                to=100, 
                number_of_steps=9, 
                variable=self.recall_limit_var
            )
            recall_limit_slider.grid(row=0, column=1, padx=10, pady=10)
            
            recall_limit_value = ctk.CTkLabel(self.gov_param_frame, textvariable=self.recall_limit_var)
            recall_limit_value.grid(row=0, column=2, padx=5, pady=10)
            
            search_label = ctk.CTkLabel(self.gov_param_frame, text="Search Term:")
            search_label.grid(row=0, column=3, padx=10, pady=10)
            
            if not hasattr(self, 'recall_search_var'):
                self.recall_search_var = tk.StringVar(value="")
            
            recall_search_entry = ctk.CTkEntry(
                self.gov_param_frame,
                textvariable=self.recall_search_var,
                width=150
            )
            recall_search_entry.grid(row=0, column=4, padx=10, pady=10)
            
            search_info = ctk.CTkLabel(
                self.gov_param_frame,
                text="Search for exact words (case-insensitive)",
                font=ctk.CTkFont(size=10, slant="italic")
            )
            search_info.grid(row=1, column=3, columnspan=2, padx=10, pady=0, sticky="w")
            
        elif source == "Census Population":
            state_limit_label = ctk.CTkLabel(self.gov_param_frame, text="Top States:")
            state_limit_label.grid(row=0, column=0, padx=10, pady=10)
            
            if not hasattr(self, 'census_limit_var'):
                self.census_limit_var = ctk.IntVar(value=10)
            
            state_limit_slider = ctk.CTkSlider(
                self.gov_param_frame, 
                from_=5, 
                to=60, 
                number_of_steps=55, 
                variable=self.census_limit_var
            )
            state_limit_slider.grid(row=0, column=1, padx=10, pady=10)
            
            state_limit_value = ctk.CTkLabel(self.gov_param_frame, textvariable=self.census_limit_var)
            state_limit_value.grid(row=0, column=2, padx=5, pady=10)
            
            if not hasattr(self, 'show_all_states_var'):
                self.show_all_states_var = ctk.BooleanVar(value=False)
            
            show_all_checkbox = ctk.CTkCheckBox(
                self.gov_param_frame,
                text="Show All States",
                variable=self.show_all_states_var
            )
            show_all_checkbox.grid(row=0, column=3, padx=10, pady=10)
    
    def setup_flights_tab(self):
        header = ctk.CTkLabel(self.tab_flights, text="Flight Data Dashboard", font=ctk.CTkFont(size=20, weight="bold"))
        header.pack(pady=10)
        
        control_frame = ctk.CTkFrame(self.tab_flights)
        control_frame.pack(fill="x", padx=20, pady=10)
        
        type_label = ctk.CTkLabel(control_frame, text="Data Type:")
        type_label.grid(row=0, column=0, padx=10, pady=10)
        
        types = [
            "Real-time Flights",
            "Airports",
            "Airlines",
            "Historical Flights"
        ]
        self.flight_type_var = ctk.StringVar(value=types[0])
        type_dropdown = ctk.CTkOptionMenu(control_frame, values=types, variable=self.flight_type_var)
        type_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
        status_label = ctk.CTkLabel(control_frame, text="Flight Status:")
        status_label.grid(row=0, column=2, padx=10, pady=10)
        
        statuses = ["", "scheduled", "active", "landed", "cancelled", "incident", "diverted"]
        self.flight_status_var = ctk.StringVar(value="")
        status_dropdown = ctk.CTkOptionMenu(control_frame, values=statuses, variable=self.flight_status_var)
        status_dropdown.grid(row=0, column=3, padx=10, pady=10)
        
        city_label = ctk.CTkLabel(control_frame, text="Departure City:")
        city_label.grid(row=1, column=0, padx=10, pady=10)
        
        cities = [
            "",
            "Atlanta",
            "Albany",
            "Annapolis",
            "Augusta",
            "Austin",
            "Baton Rouge",
            "Bismarck",
            "Boise",
            "Boston",
            "Carson City",
            "Charleston",
            "Cheyenne",
            "Chicago",
            "Columbia",
            "Columbus",
            "Concord",
            "Denver",
            "Des Moines",
            "Detroit",
            "Dover",
            "Frankfort",
            "Harrisburg",
            "Hartford",
            "Helena",
            "Honolulu",
            "Indianapolis",
            "Jackson",
            "Jefferson City",
            "Juneau",
            "Lansing",
            "Lincoln",
            "Little Rock",
            "Los Angeles",
            "Madison",
            "Montgomery",
            "Montpelier",
            "Nashville",
            "New York",
            "Oklahoma City",
            "Olympia",
            "Phoenix",
            "Pierre",
            "Providence",
            "Raleigh",
            "Richmond",
            "Sacramento",
            "Saint Paul",
            "Salem",
            "Salt Lake City",
            "San Francisco",
            "Santa Fe",
            "Springfield",
            "Tallahassee",
            "Topeka",
            "Trenton",
            "Washington DC",
            "London",
            "Paris",
            "Tokyo",
            "Beijing",
            "Sydney",
            "Dubai",
            "Toronto",
            "Mexico City",
            "Berlin",
            "Madrid"
        ]
        self.flight_city_var = ctk.StringVar(value="")
        city_dropdown = ctk.CTkOptionMenu(control_frame, values=cities, variable=self.flight_city_var)
        city_dropdown.grid(row=1, column=1, padx=10, pady=10)
        
        limit_label = ctk.CTkLabel(control_frame, text="Limit:")
        limit_label.grid(row=1, column=2, padx=10, pady=10)
        
        self.flight_limit_var = ctk.IntVar(value=10)
        limit_slider = ctk.CTkSlider(control_frame, from_=5, to=100, number_of_steps=19, variable=self.flight_limit_var)
        limit_slider.grid(row=1, column=3, padx=10, pady=10)
        
        limit_value = ctk.CTkLabel(control_frame, textvariable=self.flight_limit_var)
        limit_value.grid(row=1, column=4, padx=5, pady=10)
        
        fetch_button = ctk.CTkButton(control_frame, text="Fetch Flight Data", command=self.fetch_flights)
        fetch_button.grid(row=1, column=5, padx=20, pady=10)
        
        self.flight_content_frame = ctk.CTkFrame(self.tab_flights)
        self.flight_content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        placeholder = ctk.CTkLabel(self.flight_content_frame, text="Select data type and fetch to see results")
        placeholder.pack(pady=50)
    
    def auto_save(self, data, module_name, format="csv"):
        try:
            if data is None or data.empty:
                print(f"No {module_name} data to save")
                return None
                
            import os
            results_dir = os.path.join(os.getcwd(), "Results")
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{module_name}_{timestamp}.{format}"
            filepath = os.path.join(results_dir, filename)
            
            if format.lower() == "csv":
                data.to_csv(filepath, index=False)
            elif format.lower() == "json":
                data.to_json(filepath, orient="records", indent=4)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"Results automatically saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error auto-saving results: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_news(self):
        if not self.news_client:
            self.show_error("News API client not initialized. Check your API key.")
            return
        
        try:
            query = self.news_search_var.get()
            category = self.news_category_var.get() or None
            country = self.news_country_var.get() or None
            title_only = self.news_title_only_var.get()
            
            from datetime import datetime, timedelta
            to_date = datetime.now().date().strftime("%Y-%m-%d")
            days_back = self.news_days_back_var.get()
            from_date = (datetime.now().date() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            for widget in self.news_table_frame.winfo_children():
                widget.destroy()
            
            for widget in self.news_chart_frame.winfo_children():
                widget.destroy()
                
            for widget in self.news_wordcloud_tab.winfo_children():
                widget.destroy()
                
            for widget in self.news_treemap_tab.winfo_children():
                widget.destroy()
            
            loading_label = ctk.CTkLabel(self.news_table_frame, text="Loading news data...")
            loading_label.pack(pady=50)
            self.update_idletasks()
            
            date_info = f" ({from_date} to {to_date})"
            
            if query:
                if title_only:
                    news_data = self.news_client.get_everything_in_title(
                        query=query, 
                        page_size=50, 
                        from_date=from_date, 
                        to_date=to_date
                    )
                    title = f"Articles with '{query}' in Title{date_info}"
                else:
                    news_data = self.news_client.get_everything(
                        query=query, 
                        page_size=30, 
                        from_date=from_date, 
                        to_date=to_date
                    )
                    title = f"Search Results for '{query}'{date_info}"
            else:
                news_data = self.news_client.get_top_headlines(country=country, category=category, page_size=30)
                title = "Top Headlines"
                if category:
                    title += f" - {category.capitalize()}"
                if country:
                    title += f" ({country.upper()})"
            
            self.news_data = news_data
            
            if not news_data.empty:
                self.auto_save(news_data, "news")
            
            loading_label.destroy()
            
            if news_data.empty:
                no_data_message = "No news articles found matching your criteria."
                if from_date or to_date:
                    no_data_message += f"\nTry adjusting your date range: {date_info}"
                
                no_data_label = ctk.CTkLabel(self.news_table_frame, text=no_data_message)
                no_data_label.pack(pady=50)
                
                no_wordcloud_label = ctk.CTkLabel(self.news_wordcloud_tab, text="No data available for visualization.")
                no_wordcloud_label.pack(pady=50)
                
                no_treemap_label = ctk.CTkLabel(self.news_treemap_tab, text="No data available for treemap.")
                no_treemap_label.pack(pady=50)
                
                return
            
            table_label = ctk.CTkLabel(self.news_table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
            table_label.pack(pady=10)
            
            display_data = news_data[['title', 'source_name', 'publishedAt']].copy()
            display_data.columns = ['Title', 'Source', 'Published At']
            
            DataVisualization.create_data_table(display_data, self.news_table_frame, max_rows=15)
            
            chart_label = ctk.CTkLabel(self.news_chart_frame, text="Source Distribution", font=ctk.CTkFont(size=16, weight="bold"))
            chart_label.pack(pady=10)
            
            source_counts = news_data['source_name'].value_counts().reset_index()
            source_counts.columns = ['Source', 'Count']
            
            if len(source_counts) > 10:
                source_counts = source_counts.head(10)
            
            if len(source_counts) > 1:
                DataVisualization.create_pie_chart(
                    source_counts, 
                    'Source', 
                    'Count', 
                    'Articles per Source', 
                    self.news_chart_frame
                )
            else:
                single_source_label = ctk.CTkLabel(self.news_chart_frame, text="All articles from a single source")
                single_source_label.pack(pady=50)
            
            wordcloud_title = ctk.CTkLabel(
                self.news_wordcloud_tab, 
                text="Word Cloud of Article Titles", 
                font=ctk.CTkFont(size=16, weight="bold")
            )
            wordcloud_title.pack(pady=10)
            
            wordcloud_explanation = ctk.CTkLabel(
                self.news_wordcloud_tab,
                text="This visualization shows the most common words in article titles, with size representing frequency.",
                font=ctk.CTkFont(size=12)
            )
            wordcloud_explanation.pack(pady=5)
            
            wordcloud_frame = ctk.CTkFrame(self.news_wordcloud_tab)
            wordcloud_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            if 'title' in news_data.columns:
                DataVisualization.create_wordcloud(
                    text_data=news_data['title'],
                    title="Word Frequency in Headlines",
                    frame=wordcloud_frame,
                    figsize=(10, 6)
                )
            else:
                no_titles_label = ctk.CTkLabel(wordcloud_frame, text="Title data not available for word cloud.")
                no_titles_label.pack(pady=50)
            
            treemap_title = ctk.CTkLabel(
                self.news_treemap_tab, 
                text="Sources Treemap Visualization", 
                font=ctk.CTkFont(size=16, weight="bold")
            )
            treemap_title.pack(pady=10)
            
            treemap_explanation = ctk.CTkLabel(
                self.news_treemap_tab,
                text="This visualization shows news sources with box size representing number of articles.",
                font=ctk.CTkFont(size=12)
            )
            treemap_explanation.pack(pady=5)
            
            treemap_frame = ctk.CTkFrame(self.news_treemap_tab)
            treemap_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            if len(source_counts) > 1:
                DataVisualization.create_treemap(
                    data=source_counts,
                    labels_column='Source',
                    values_column='Count',
                    title="News Source Distribution (Box Size = Number of Articles)",
                    frame=treemap_frame,
                    figsize=(10, 6)
                )
            else:
                single_source_treemap_label = ctk.CTkLabel(treemap_frame, text="Not enough different sources for a treemap.")
                single_source_treemap_label.pack(pady=50)
            
        except Exception as e:
            self.show_error(f"Error fetching news: {e}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def fetch_reddit(self):
        if not self.reddit_client:
            self.show_error("Reddit client not initialized. Check your API keys.")
            return
        
        try:
            query = self.reddit_search_var.get()
            subreddit = self.reddit_subreddit_var.get() or None
            sort_type = self.reddit_sort_var.get()
            count = self.reddit_count_var.get()
            
            for widget in self.reddit_left_frame.winfo_children():
                widget.destroy()
            
            for widget in self.reddit_right_frame.winfo_children():
                widget.destroy()
            
            loading_label = ctk.CTkLabel(self.reddit_left_frame, text="Loading Reddit data...")
            loading_label.pack(pady=50)
            self.update_idletasks()
            
            posts_data = self.reddit_client.search_posts(
                query=query,
                subreddit=subreddit,
                limit=count,
                sort=sort_type
            )
            
            self.reddit_data = posts_data
            
            if not posts_data.empty:
                self.auto_save(posts_data, "reddit")
            
            loading_label.destroy()
            
            if posts_data.empty:
                no_data_label = ctk.CTkLabel(self.reddit_left_frame, text="No posts found matching your criteria.")
                no_data_label.pack(pady=50)
                return
            
            title_text = "Reddit Posts"
            if subreddit:
                title_text += f" from r/{subreddit}"
            if query and sort_type == "search":
                title_text += f" matching '{query}'"
            
            table_label = ctk.CTkLabel(self.reddit_left_frame, text=title_text, font=ctk.CTkFont(size=16, weight="bold"))
            table_label.pack(pady=10)
            
            display_data = posts_data[['title', 'subreddit', 'score', 'num_comments', 'author']].copy()
            display_data.columns = ['Title', 'Subreddit', 'Score', 'Comments', 'Author']
            
            DataVisualization.create_data_table(display_data, self.reddit_left_frame, max_rows=0)
            
            score_label = ctk.CTkLabel(self.reddit_right_frame, text="Post Score Distribution", font=ctk.CTkFont(size=16, weight="bold"))
            score_label.pack(pady=10)
            
            histogram_frame = ctk.CTkFrame(self.reddit_right_frame)
            histogram_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            if len(posts_data) > 1:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.hist(posts_data['score'], bins=10, color='#3B8ED0')
                ax.set_title('Post Score Distribution')
                ax.set_xlabel('Score')
                ax.set_ylabel('Number of Posts')
                plt.tight_layout()
                
                canvas = FigureCanvasTkAgg(fig, master=histogram_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill='both', expand=True)
            else:
                insufficient_data_label = ctk.CTkLabel(histogram_frame, text="Not enough data for histogram")
                insufficient_data_label.pack(pady=50)
            
            engagement_label = ctk.CTkLabel(self.reddit_right_frame, text="Comments vs Score", font=ctk.CTkFont(size=16, weight="bold"))
            engagement_label.pack(pady=10)
            
            scatter_frame = ctk.CTkFrame(self.reddit_right_frame)
            scatter_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            DataVisualization.create_scatter_plot(
                posts_data,
                'score',
                'num_comments',
                'Comments vs Score',
                'Score',
                'Comments',
                scatter_frame
            )
        except Exception as e:
            self.show_error(f"Error fetching Reddit data: {e}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def fetch_government(self):
        if not self.gov_client:
            self.show_error("Government data client not initialized. Check your API key.")
            return
        
        try:
            source = self.gov_source_var.get()
            
            for widget in self.gov_content_frame.winfo_children():
                widget.destroy()
            
            loading_label = ctk.CTkLabel(self.gov_content_frame, text="Loading government data...")
            loading_label.pack(pady=50)
            self.update_idletasks()
            
            if source == "FDA Food Recalls":
                recall_limit = self.recall_limit_var.get() if hasattr(self, 'recall_limit_var') else 25
                
                search_term = self.recall_search_var.get() if hasattr(self, 'recall_search_var') else ""
                
                if search_term:
                    loading_search_label = ctk.CTkLabel(self.gov_content_frame, text=f"Searching entire FDA database for '{search_term}'...")
                    loading_search_label.pack(pady=20)
                    self.update_idletasks()
                    
                    gov_data = self.gov_client.search_fda_food_recalls(search_term=search_term, max_results=recall_limit)
                    
                    loading_search_label.destroy()
                    
                    if gov_data.empty:
                        no_results_label = ctk.CTkLabel(
                            self.gov_content_frame, 
                            text=f"No FDA recalls found matching '{search_term}'. Try a different search term.",
                            font=ctk.CTkFont(size=14, weight="bold")
                        )
                        no_results_label.pack(pady=50)
                        return
                    
                    title = f"FDA Food Recalls - Search: '{search_term}' ({len(gov_data)} results)"
                else:
                    gov_data = self.gov_client.get_fda_food_recalls(limit=recall_limit)
                    title = f"FDA Food Recalls ({len(gov_data)} results)"
                
                if not gov_data.empty:
                    self.auto_save(gov_data, "fda_recalls")
                
                content_container = ctk.CTkFrame(self.gov_content_frame)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                viz_tabview = ctk.CTkTabview(content_container, width=1120, height=680)
                viz_tabview.pack(fill="both", expand=True, padx=5, pady=5)
                
                tab_details = viz_tabview.add("Details & Status")
                tab_firms = viz_tabview.add("Recalling Firms")
                
                viz_tabview.set("Details & Status")
                
                if not gov_data.empty:
                    details_frame = ctk.CTkFrame(tab_details)
                    details_frame.pack(fill="both", expand=True, padx=5, pady=5)
                    
                    table_frame = ctk.CTkFrame(details_frame)
                    table_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                    
                    chart_frame = ctk.CTkFrame(details_frame)
                    chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
                    
                    table_title = ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                    table_title.pack(pady=10)
                    
                    if 'product_description' in gov_data.columns:
                        if 'recall_initiation_date' in gov_data.columns:
                            gov_data['formatted_date'] = gov_data['recall_initiation_date'].apply(
                                lambda x: f"{x[:4]}-{x[4:6]}-{x[6:]}" if len(str(x)) == 8 else x
                            )
                        else:
                            gov_data['formatted_date'] = "Unknown"
                        
                        display_data = gov_data[['product_description', 'formatted_date', 'reason_for_recall', 
                                                'status', 'recalling_firm', 'classification']].copy()
                        display_data.columns = ['Product', 'Date', 'Reason', 'Status', 'Firm', 'Classification']
                        
                        DataVisualization.create_data_table(display_data, table_frame, max_rows=20)
                        
                        chart_title_text = "Recalls by Status"
                        if search_term:
                            chart_title_text += f" - Search: '{search_term}'"
                            
                        chart_title = ctk.CTkLabel(chart_frame, text=chart_title_text, font=ctk.CTkFont(size=16, weight="bold"))
                        chart_title.pack(pady=10)
                        
                        status_counts = gov_data['status'].value_counts().reset_index()
                        status_counts.columns = ['Status', 'Count']
                        
                        DataVisualization.create_pie_chart(
                            status_counts,
                            'Status',
                            'Count',
                            f"Recall Status Distribution (Total: {len(gov_data)} Recalls)",
                            chart_frame
                        )
                        
                        if 'classification' in gov_data.columns:
                            class_frame = ctk.CTkFrame(chart_frame)
                            class_frame.pack(fill="both", expand=True, padx=5, pady=15)
                            
                            class_title = ctk.CTkLabel(class_frame, text="Recalls by Classification", 
                                                     font=ctk.CTkFont(size=16, weight="bold"))
                            class_title.pack(pady=10)
                            
                            class_info = ctk.CTkLabel(class_frame, text="Class I: Dangerous/life-threatening\nClass II: May cause temporary issues\nClass III: Not likely to cause harm", 
                                                    font=ctk.CTkFont(size=12, slant="italic"))
                            class_info.pack(pady=5)
                            
                            class_counts = gov_data['classification'].value_counts().reset_index()
                            class_counts.columns = ['Classification', 'Count']
                            
                            DataVisualization.create_bar_chart(
                                class_counts,
                                'Classification',
                                'Count',
                                "Recall Classification Distribution",
                                'Classification',
                                'Number of Recalls',
                                class_frame
                            )
                    
                    firms_frame = ctk.CTkFrame(tab_firms)
                    firms_frame.pack(fill="both", expand=True, padx=10, pady=10)
                    
                    firms_title = ctk.CTkLabel(firms_frame, text="Top Recalling Firms", 
                                              font=ctk.CTkFont(size=16, weight="bold"))
                    firms_title.pack(pady=10)
                    
                    if 'recalling_firm' in gov_data.columns:
                        firm_counts = gov_data['recalling_firm'].value_counts().reset_index()
                        firm_counts.columns = ['Firm', 'Count']
                        
                        top_firms = firm_counts.head(10)
                        
                        if len(top_firms) > 1:
                            firms_chart_frame = ctk.CTkFrame(firms_frame)
                            firms_chart_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                            
                            reasons_chart_frame = ctk.CTkFrame(firms_frame)
                            reasons_chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
                            
                            DataVisualization.create_bar_chart(
                                top_firms,
                                'Firm',
                                'Count',
                                "Top 10 Firms with Most Recalls",
                                'Firm',
                                'Number of Recalls',
                                firms_chart_frame
                            )
                            
                            if 'reason_for_recall' in gov_data.columns:
                                reasons_title = ctk.CTkLabel(reasons_chart_frame, text="Common Recall Reasons", 
                                                          font=ctk.CTkFont(size=16, weight="bold"))
                                reasons_title.pack(pady=10)
                                
                                gov_data['reason_category'] = gov_data['reason_for_recall'].apply(self._categorize_recall_reason)
                                
                                reason_counts = gov_data['reason_category'].value_counts().reset_index()
                                reason_counts.columns = ['Reason', 'Count']
                                
                                top_reasons = reason_counts.head(8)
                                
                                if len(top_reasons) > 1:
                                    DataVisualization.create_pie_chart(
                                        top_reasons,
                                        'Reason',
                                        'Count',
                                        "Common Recall Reasons",
                                        reasons_chart_frame
                                    )
                                else:
                                    reasons_note = ctk.CTkLabel(reasons_chart_frame, text="Not enough data for reasons chart")
                                    reasons_note.pack(pady=50)
                        else:
                            firms_note = ctk.CTkLabel(firms_frame, text="Not enough data to display firm statistics")
                            firms_note.pack(pady=50)
                    else:
                        firms_note = ctk.CTkLabel(firms_frame, text="Firm information not available")
                        firms_note.pack(pady=50)
                else:
                    no_cols_label = ctk.CTkLabel(tab_details, text="Required columns not found in data.")
                    no_cols_label.pack(pady=50)
                
            elif source == "Census Population":
                gov_data = self.gov_client.get_census_population_data()
                title = "US Census Population Data"
                
                if not gov_data.empty:
                    self.auto_save(gov_data, "census_population")
                
                content_container = ctk.CTkFrame(self.gov_content_frame)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                table_frame = ctk.CTkFrame(content_container)
                table_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                chart_frame = ctk.CTkFrame(content_container)
                chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
                
                if not gov_data.empty:
                    table_title = ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                    table_title.pack(pady=10)
                    
                    if 'POP' in gov_data.columns:
                        gov_data['POP'] = pd.to_numeric(gov_data['POP'], errors='coerce')
                    
                    if 'NAME' in gov_data.columns and 'POP' in gov_data.columns:
                        gov_data = gov_data.sort_values('POP', ascending=False)
                    
                    DataVisualization.create_data_table(gov_data, table_frame, max_rows=0)
                    
                    show_all = self.show_all_states_var.get() if hasattr(self, 'show_all_states_var') else False
                    state_limit = None if show_all else self.census_limit_var.get() if hasattr(self, 'census_limit_var') else 10
                    
                    chart_title_text = "States by Population"
                    if not show_all and state_limit:
                        chart_title_text = f"Top {state_limit} States by Population"
                    
                    chart_title = ctk.CTkLabel(chart_frame, text=chart_title_text, font=ctk.CTkFont(size=16, weight="bold"))
                    chart_title.pack(pady=10)
                    
                    if 'NAME' in gov_data.columns and 'POP' in gov_data.columns:
                        if not show_all and state_limit:
                            population_data = gov_data[['NAME', 'POP']].head(state_limit)
                        else:
                            population_data = gov_data[['NAME', 'POP']]
                        
                        population_data.columns = ['State', 'Population']
                        
                        DataVisualization.create_bar_chart(
                            population_data,
                            'State',
                            'Population',
                            chart_title_text,
                            'State',
                            'Population',
                            chart_frame
                        )
                    else:
                        no_cols_label = ctk.CTkLabel(chart_frame, text="Required columns not found in data.")
                        no_cols_label.pack(pady=50)
                
            loading_label.destroy()
            
            if gov_data.empty:
                no_data_label = ctk.CTkLabel(self.gov_content_frame, text="No data found for the selected source.")
                no_data_label.pack(pady=50)
        
        except Exception as e:
            self.show_error(f"Error fetching government data: {e}")
            print(f"Error details: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _categorize_recall_reason(self, reason_text):
        reason_lower = str(reason_text).lower()
        
        if "allergen" in reason_lower or "allergy" in reason_lower:
            return "Undeclared Allergen"
        elif "listeria" in reason_lower:
            return "Listeria"
        elif "salmonella" in reason_lower:
            return "Salmonella"
        elif "e. coli" in reason_lower or "escherichia" in reason_lower:
            return "E. coli"
        elif "foreign" in reason_lower and ("material" in reason_lower or "object" in reason_lower):
            return "Foreign Material"
        elif "mislabel" in reason_lower or "misbranded" in reason_lower:
            return "Mislabeling"
        elif "undeclared" in reason_lower:
            return "Undeclared Ingredients"
        elif "contamina" in reason_lower:
            return "Contamination"
        else:
            return "Other"
    
    def fetch_flights(self):
        if not self.flight_client:
            self.show_error("Flight data client not initialized. Check your API key.")
            return
        
        try:
            data_type = self.flight_type_var.get()
            flight_status = self.flight_status_var.get() or None
            departure_city = self.flight_city_var.get() or None
            limit = self.flight_limit_var.get()
            
            for widget in self.flight_content_frame.winfo_children():
                widget.destroy()
            
            loading_label = ctk.CTkLabel(self.flight_content_frame, text="Loading flight data...")
            loading_label.pack(pady=50)
            self.update_idletasks()
            
            if data_type == "Real-time Flights":
                print(f"Fetching flight data with: status={flight_status}, city={departure_city}, limit={limit}")
                flight_data = self.flight_client.get_real_time_flights(
                    limit=limit,
                    flight_status=flight_status,
                    departure_city=departure_city
                )
                print(f"API response - data rows: {len(flight_data) if not flight_data.empty else 0}")
                print(f"Data columns: {flight_data.columns.tolist() if not flight_data.empty else 'No data'}")
                
                if not flight_data.empty:
                    self.auto_save(flight_data, "realtime_flights")
                
                title = "Real-time Flight Data"
                if flight_status:
                    title += f" - {flight_status.capitalize()} Flights"
                if departure_city:
                    title += f" from {departure_city}"
                
                flight_tabview = ctk.CTkTabview(self.flight_content_frame, width=1120, height=650)
                flight_tabview.pack(fill="both", expand=True, padx=10, pady=10)
                
                data_tab = flight_tabview.add("Flight Info")
                map_tab = flight_tabview.add("World Map")
                
                flight_tabview.set("World Map")
                
                content_container = ctk.CTkFrame(data_tab)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                table_frame = ctk.CTkFrame(content_container)
                table_frame.pack(fill="both", expand=True, padx=5, pady=5)
                
                table_title = ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                table_title.pack(pady=10)
                
                if flight_data.empty:
                    loading_label.destroy()
                    
                    no_data_label = ctk.CTkLabel(self.flight_content_frame, 
                                                text=f"No flight data found matching your criteria.\n"
                                                     f"Try adjusting your filters.")
                    no_data_label.pack(pady=50)
                    return
                
                if not flight_data.empty:
                    columns_to_display = [
                        'flight_iata', 'airline_name', 'departure_airport', 
                        'arrival_airport', 'flight_status', 'departure_scheduled'
                    ]
                    
                    available_columns = [col for col in columns_to_display if col in flight_data.columns]
                    
                    if available_columns:
                        display_data = flight_data[available_columns].copy()
                        
                        column_mapping = {
                            'flight_iata': 'Flight',
                            'airline_name': 'Airline',
                            'departure_airport': 'From',
                            'arrival_airport': 'To',
                            'flight_status': 'Status',
                            'departure_scheduled': 'Scheduled'
                        }
                        
                        display_data.rename(columns=column_mapping, inplace=True)
                        
                        DataVisualization.create_data_table(display_data, table_frame, max_rows=0)
                    
                    map_title = ctk.CTkLabel(map_tab, text="Flight Routes Map", font=ctk.CTkFont(size=16, weight="bold"))
                    map_title.pack(pady=10)
                    
                    required_cols = ['departure_airport', 'arrival_airport']
                    
                    has_airport_data = all(col in flight_data.columns for col in required_cols)
                    
                    if has_airport_data:
                        print(f"Creating map with {len(flight_data)} flight records")
                        flight_tabview.set("World Map")
                        self.create_route_map(flight_data, map_tab)
                    else:
                        missing_cols = [col for col in required_cols if col not in flight_data.columns]
                        print(f"Missing columns for map: {missing_cols}")
                        no_map_label = ctk.CTkLabel(map_tab, text="Map cannot be displayed. Airport data is missing.")
                        no_map_label.pack(pady=50)
            
            elif data_type == "Airports":
                flight_data = self.flight_client.get_airport_data(limit=limit)
                
                if not flight_data.empty:
                    self.auto_save(flight_data, "airports")
                    
                title = "Airport Data"
                
                content_container = ctk.CTkFrame(self.flight_content_frame)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                if not flight_data.empty:
                    table_title = ctk.CTkLabel(content_container, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                    table_title.pack(pady=10)
                    
                    columns_to_display = [
                        'airport_name', 'iata_code', 'country_name', 
                        'city_name', 'timezone'
                    ]
                    
                    available_columns = [col for col in columns_to_display if col in flight_data.columns]
                    
                    if available_columns:
                        display_data = flight_data[available_columns].copy()
                        
                        DataVisualization.create_data_table(display_data, content_container, max_rows=20)
                    else:
                        no_cols_label = ctk.CTkLabel(content_container, text="Required columns not found in data.")
                        no_cols_label.pack(pady=50)
            
            elif data_type == "Airlines":
                flight_data = self.flight_client.get_airline_data(limit=limit)
                
                if not flight_data.empty:
                    self.auto_save(flight_data, "airlines")
                    
                title = "Airline Data"
                
                content_container = ctk.CTkFrame(self.flight_content_frame)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                if not flight_data.empty:
                    table_title = ctk.CTkLabel(content_container, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                    table_title.pack(pady=10)
                    
                    columns_to_display = [
                        'airline_name', 'iata_code', 'icao_code',
                        'country_name', 'fleet_size', 'status'
                    ]
                    
                    available_columns = [col for col in columns_to_display if col in flight_data.columns]
                    
                    if available_columns:
                        display_data = flight_data[available_columns].copy()
                        
                        DataVisualization.create_data_table(display_data, content_container, max_rows=20)
                    else:
                        no_cols_label = ctk.CTkLabel(content_container, text="Required columns not found in data.")
                        no_cols_label.pack(pady=50)
            
            elif data_type == "Historical Flights":
                from datetime import datetime, timedelta
                yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                
                flight_data = self.flight_client.get_historical_flights(
                    flight_date=yesterday,
                    limit=limit
                )
                
                if not flight_data.empty:
                    self.auto_save(flight_data, "historical_flights")
                    
                title = f"Historical Flight Data - {yesterday}"
                
                content_container = ctk.CTkFrame(self.flight_content_frame)
                content_container.pack(fill="both", expand=True, padx=10, pady=10)
                
                table_frame = ctk.CTkFrame(content_container)
                table_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
                
                chart_frame = ctk.CTkFrame(content_container)
                chart_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
                
                if not flight_data.empty:
                    table_title = ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
                    table_title.pack(pady=10)
                    
                    columns_to_display = [
                        'flight_iata', 'airline_name', 'departure_airport', 
                        'arrival_airport', 'flight_status'
                    ]
                    
                    available_columns = [col for col in columns_to_display if col in flight_data.columns]
                    
                    if available_columns:
                        display_data = flight_data[available_columns].copy()
                        
                        column_mapping = {
                            'flight_iata': 'Flight',
                            'airline_name': 'Airline',
                            'departure_airport': 'From',
                            'arrival_airport': 'To',
                            'flight_status': 'Status'
                        }
                        
                        rename_dict = {k: v for k, v in column_mapping.items() if k in available_columns}
                        display_data.rename(columns=rename_dict, inplace=True)
                        
                        DataVisualization.create_data_table(display_data, table_frame, max_rows=15)
                        
                        if 'flight_status' in flight_data.columns:
                            chart_title = ctk.CTkLabel(chart_frame, text="Historical Flight Status", font=ctk.CTkFont(size=16, weight="bold"))
                            chart_title.pack(pady=10)
                            
                            status_counts = flight_data['flight_status'].value_counts().reset_index()
                            status_counts.columns = ['Status', 'Count']
                            
                            DataVisualization.create_pie_chart(
                                status_counts,
                                'Status',
                                'Count',
                                'Historical Flight Status Distribution',
                                chart_frame
                            )
                    else:
                        no_cols_label = ctk.CTkLabel(table_frame, text="Required columns not found in data.")
                        no_cols_label.pack(pady=50)
            
            loading_label.destroy()
            
        except Exception as e:
            loading_label.destroy() if 'loading_label' in locals() else None
            self.show_error(f"Error fetching flight data: {str(e)}")
            
    def create_route_map(self, flight_data, parent_frame):
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import numpy as np
            from mpl_toolkits.basemap import Basemap
            
            required_cols = ['departure_airport', 'arrival_airport']
            
            missing_cols = [col for col in required_cols if col not in flight_data.columns]
            if missing_cols:
                error_frame = ctk.CTkFrame(parent_frame)
                error_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                error_msg = f"Missing data columns needed for map: {', '.join(missing_cols)}"
                error_label = ctk.CTkLabel(error_frame, text=error_msg)
                error_label.pack(pady=50)
                return
                
            map_data = flight_data.dropna(subset=required_cols)
            
            if map_data.empty:
                no_data_label = ctk.CTkLabel(parent_frame, text="No route data available for mapping.")
                no_data_label.pack(pady=50)
                return
            
            loading_frame = ctk.CTkFrame(parent_frame)
            loading_frame.pack(fill="x", padx=10, pady=5)
            
            loading_label = ctk.CTkLabel(
                loading_frame, 
                text="Fetching coordinates for airports... This may take a moment.",
                font=ctk.CTkFont(size=12)
            )
            loading_label.pack(pady=5)
            self.update_idletasks()
            
            airport_coords = {}
            unique_airports = set()
            
            for _, flight in map_data.iterrows():
                dep_airport = str(flight['departure_airport'])
                arr_airport = str(flight['arrival_airport'])
                unique_airports.add(dep_airport)
                unique_airports.add(arr_airport)
            
            loading_label.configure(text=f"Fetching coordinates for {len(unique_airports)} airports...")
            self.update_idletasks()
            
            for airport in unique_airports:
                if airport and airport != "nan":
                    coords = self.get_airport_coordinates(airport)
                    if coords:
                        airport_coords[airport] = coords
                    
                    loading_label.configure(text=f"Looking up airports... ({len(airport_coords)}/{len(unique_airports)})")
                    self.update_idletasks()
            
            if len(airport_coords) < 2:
                loading_frame.destroy()
                error_label = ctk.CTkLabel(
                    parent_frame, 
                    text=f"Could not find enough airport coordinates. Found {len(airport_coords)} out of {len(unique_airports)}.",
                    font=ctk.CTkFont(size=14)
                )
                error_label.pack(pady=50)
                return
            
            loading_frame.destroy()
            info_frame = ctk.CTkFrame(parent_frame)
            info_frame.pack(fill="x", padx=10, pady=5)
            
            info_label = ctk.CTkLabel(
                info_frame, 
                text=f"Showing flight routes with {len(airport_coords)} airports • Blue lines connect departure (red) to arrival (green) airports",
                font=ctk.CTkFont(size=12)
            )
            info_label.pack(pady=5)
                
            fig = plt.Figure(figsize=(12, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            m = Basemap(projection='robin', lon_0=0, resolution='l', ax=ax)
            
            m.drawcoastlines(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            m.fillcontinents(color='lightgray', lake_color='white')
            m.drawmapboundary(fill_color='white')
            
            m.drawparallels(np.arange(-90., 91., 30.), labels=[1, 0, 0, 0])
            m.drawmeridians(np.arange(-180., 181., 60.), labels=[0, 0, 0, 1])
            
            plotted_airports = set()
            
            routes_plotted = 0
            
            for idx, flight in map_data.iterrows():
                try:
                    dep_airport = str(flight['departure_airport'])
                    arr_airport = str(flight['arrival_airport'])
                    
                    if dep_airport not in airport_coords or arr_airport not in airport_coords:
                        continue
                    
                    start_lat, start_lon = airport_coords[dep_airport]
                    end_lat, end_lon = airport_coords[arr_airport]
                    
                    flight_number = str(flight.get('flight_iata', '')) 
                    
                    x1, y1 = m(start_lon, start_lat)
                    x2, y2 = m(end_lon, end_lat)
                    
                    m.drawgreatcircle(
                        start_lon, start_lat, 
                        end_lon, end_lat, 
                        linewidth=1.5, 
                        color='blue', 
                        alpha=0.7
                    )
                    routes_plotted += 1
                    
                    if dep_airport not in plotted_airports:
                        m.plot(x1, y1, 'ro', markersize=6, alpha=0.8)
                        plotted_airports.add(dep_airport)
                        
                        if len(plotted_airports) < 20:
                            plt.annotate(
                                dep_airport,
                                xy=(x1, y1),
                                xytext=(5, 5),
                                textcoords="offset points",
                                fontsize=8,
                                color='darkred'
                            )
                    
                    if arr_airport not in plotted_airports:
                        m.plot(x2, y2, 'go', markersize=6, alpha=0.8)
                        plotted_airports.add(arr_airport)
                        
                        if len(plotted_airports) < 20:
                            plt.annotate(
                                arr_airport,
                                xy=(x2, y2),
                                xytext=(5, 5),
                                textcoords="offset points",
                                fontsize=8,
                                color='darkgreen'
                            )
                        
                except Exception as e:
                    print(f"Error plotting route {idx}: {e}")
                    continue
            
            info_label.configure(text=f"Showing {routes_plotted} flight routes with {len(plotted_airports)} airports • Blue lines connect departure (red) to arrival (green) airports")
            
            ax.set_title('Flight Routes Map')
            
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='r', markersize=8, label='Departure Airports'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='g', markersize=8, label='Arrival Airports'),
                Line2D([0], [0], color='blue', alpha=0.7, label='Flight Routes')
            ]
            ax.legend(handles=legend_elements, loc='lower left')
            
            canvas = FigureCanvasTkAgg(fig, master=parent_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            
            self.create_route_details_table(map_data, parent_frame)
            
        except ImportError:
            error_frame = ctk.CTkFrame(parent_frame)
            error_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            error_label = ctk.CTkLabel(
                error_frame, 
                text="The world map visualization requires additional packages.\n"
                     "Please install matplotlib and basemap:\n"
                     "pip install matplotlib\n"
                     "pip install basemap"
            )
            error_label.pack(pady=50)
            
        except Exception as e:
            error_frame = ctk.CTkFrame(parent_frame)
            error_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            error_msg = f"Error creating map: {str(e)}"
            error_label = ctk.CTkLabel(error_frame, text=error_msg)
            error_label.pack(pady=50)
    
    def create_route_details_table(self, flight_data, parent_frame):
        details_frame = ctk.CTkFrame(parent_frame)
        details_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            details_frame, 
            text="Flight Route Details", 
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=5)
        
        display_cols = ['flight_iata', 'airline_name', 'departure_airport', 'arrival_airport', 'flight_status']
        available_cols = [col for col in display_cols if col in flight_data.columns]
        
        if available_cols:
            display_data = flight_data[available_cols].copy()
            
            column_mapping = {
                'flight_iata': 'Flight #',
                'airline_name': 'Airline',
                'departure_airport': 'From',
                'arrival_airport': 'To',
                'flight_status': 'Status'
            }
            
            rename_dict = {k: v for k, v in column_mapping.items() if k in available_cols}
            display_data.rename(columns=rename_dict, inplace=True)
            
            DataVisualization.create_data_table(display_data, details_frame, max_rows=5)

    def show_error(self, message):
        """Show an error message dialog"""
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.transient(self)
        error_window.grab_set()
        
        error_label = ctk.CTkLabel(error_window, text=message, wraplength=350)
        error_label.pack(pady=30, padx=20)
        
        ok_button = ctk.CTkButton(error_window, text="OK", command=error_window.destroy)
        ok_button.pack(pady=20)

    def test_with_jfk(self):
        if not self.flight_client:
            self.show_error("Flight data client not initialized. Check your API key.")
            return
            
        for widget in self.flight_content_frame.winfo_children():
            widget.destroy()
        
        loading_label = ctk.CTkLabel(self.flight_content_frame, text="Testing API with JFK airport...")
        loading_label.pack(pady=50)
        self.update_idletasks()
        
        try:
            print("DIRECT JFK TEST: Bypassing city lookup logic")
            print("DIRECT JFK TEST: Making direct API call for JFK")
            
            limit = 25
            flight_status = "scheduled"
            
            flight_data = self.flight_client.get_direct_airport_flights(
                dep_iata="JFK",
                limit=limit,
                flight_status=flight_status
            )
            
            title = f"Test: JFK Airport Flights - {flight_status.capitalize()}"
            
            if flight_data.empty:
                self.show_error("No data returned even for JFK test. This indicates an API issue.\n\n"
                              "Possible causes:\n"
                              "1. API usage limit exceeded (100 calls/month)\n"
                              "2. API key not activated or invalid\n"
                              "3. Aviation Stack service is currently down")
                loading_label.destroy()
                return
                
            flight_tabview = ctk.CTkTabview(self.flight_content_frame, width=1120, height=650)
            flight_tabview.pack(fill="both", expand=True, padx=10, pady=10)
            
            data_tab = flight_tabview.add("Flight Info")
            map_tab = flight_tabview.add("World Map")
            
            flight_tabview.set("World Map")
            
            content_container = ctk.CTkFrame(data_tab)
            content_container.pack(fill="both", expand=True, padx=10, pady=10)
            
            table_frame = ctk.CTkFrame(content_container)
            table_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            table_title = ctk.CTkLabel(table_frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
            table_title.pack(pady=10)
            
            columns_to_display = [
                'flight_iata', 'airline_name', 'departure_airport', 
                'arrival_airport', 'flight_status', 'departure_scheduled'
            ]
            
            available_columns = [col for col in columns_to_display if col in flight_data.columns]
            
            if available_columns:
                display_data = flight_data[available_columns].copy()
                
                column_mapping = {
                    'flight_iata': 'Flight',
                    'airline_name': 'Airline',
                    'departure_airport': 'From',
                    'arrival_airport': 'To',
                    'flight_status': 'Status',
                    'departure_scheduled': 'Scheduled'
                }
                
                display_data.rename(columns=column_mapping, inplace=True)
                
                DataVisualization.create_data_table(display_data, table_frame, max_rows=0)
            
            map_title = ctk.CTkLabel(map_tab, text="Flight Routes from JFK", font=ctk.CTkFont(size=16, weight="bold"))
            map_title.pack(pady=10)
            
            required_cols = ['departure_airport', 'arrival_airport']
            
            has_airport_data = all(col in flight_data.columns for col in required_cols)
            
            if has_airport_data:
                print(f"Creating map with {len(flight_data)} flight records from JFK")
                flight_tabview.set("World Map")
                self.create_route_map(flight_data, map_tab)
            else:
                missing_cols = [col for col in required_cols if col not in flight_data.columns]
                print(f"Missing columns for map: {missing_cols}")
                no_map_label = ctk.CTkLabel(map_tab, text="Map cannot be displayed. Airport data is missing.")
                no_map_label.pack(pady=50)
            
            loading_label.destroy()
            
        except Exception as e:
            if 'loading_label' in locals():
                loading_label.destroy()
            self.show_error(f"Error in JFK test: {str(e)}")
            print(f"JFK Test Error details: {str(e)}")

    def get_airport_coordinates(self, airport_name):
        try:
            search_query = f"{airport_name} airport"
            print(f"Searching for coordinates of: {search_query}")
            
            import requests
            
            url = "https://nominatim.openstreetmap.org/search"
            headers = {
                'User-Agent': 'OSINT-Dashboard/1.0'
            }
            params = {
                'q': search_query,
                'format': 'json',
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                print(f"Found coordinates for {airport_name}: ({lat}, {lon})")
                return (lat, lon)
            else:
                print(f"No coordinates found for {airport_name}")
                return None
                
        except Exception as e:
            print(f"Error getting coordinates for {airport_name}: {e}")
            return None

    def open_browser(self, url):
        webbrowser.open(url)
    
    def show_info(self, message):
        info_window = ctk.CTkToplevel(self)
        info_window.title("Information")
        info_window.geometry("400x200")
        info_window.transient(self)
        info_window.grab_set()
        
        info_label = ctk.CTkLabel(info_window, text=message, wraplength=350)
        info_label.pack(pady=30, padx=20)
        
        ok_button = ctk.CTkButton(info_window, text="OK", command=info_window.destroy)
        ok_button.pack(pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop() 