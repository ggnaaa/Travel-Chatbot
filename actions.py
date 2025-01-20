import pandas as pd
import os
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

data_path = os.environ.get("TOURISM_DATA_PATH", "C:\\Gagana\\7com1\\Rasaproject\\tourism_dataset.csv")

if os.path.exists(data_path):
    try:
        df = pd.read_csv(data_path)
        print("DataFrame loaded successfully.")
        print(df.head())  # Print the first few rows
        print(df.info()) #Print information about the dataframe
        valid_categories = set(df['Category'].str.lower().unique())
        valid_countries = set(df['Country'].str.lower().unique())
    except FileNotFoundError:
        print(f"Error: tourism_dataset.csv not found at: {data_path}")
        df = pd.DataFrame()
        valid_categories = set()
        valid_countries = set()
    except pd.errors.EmptyDataError:
        print("Error: tourism_dataset.csv is empty.")
        df = pd.DataFrame()
        valid_categories = set()
        valid_countries = set()
    except pd.errors.ParserError:
        print("Error: Could not parse tourism_dataset.csv. Check the file format.")
        df = pd.DataFrame()
        valid_categories = set()
        valid_countries = set()
else:
    print(f"Error: File not found at path: {data_path}")
    df = pd.DataFrame()
    valid_categories = set()
    valid_countries = set()

famous_indian_locations = {
    "Ladakh": {"Category": "Adventure", "Rating": 4.8, "Accommodation_Available": "Yes"},
    "Rishikesh": {"Category": "Adventure", "Rating": 4.5, "Accommodation_Available": "Yes"},
    "Andaman and Nicobar Islands": {"Category": "Beach", "Rating": 4.6, "Accommodation_Available": "Yes"},
    "Varanasi": {"Category": "Historical", "Rating": 4.2, "Accommodation_Available": "Yes"},
    "Agra": {"Category": "Historical", "Rating": 4.0, "Accommodation_Available": "Yes"},
    "Delhi": {"Category": "Urban", "Rating": 3.9, "Accommodation_Available": "Yes"},
    "Goa": {"Category": "Beach", "Rating": 4.3, "Accommodation_Available": "Yes"},
    "Jaipur": {"Category": "Historical", "Rating": 4.1, "Accommodation_Available": "Yes"},
}

class ActionProvideTourismByCategory(Action):
    def name(self) -> Text:
        return "action_provide_tourism_by_category"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = tracker.get_slot("country")
        category = tracker.get_slot("category")

        if df.empty:  # Use predefined locations
            dispatcher.utter_message(text="..")

            if country and country.lower() != "india":
                dispatcher.utter_message(text=f"Sorry, I only have predefined data for India at the moment.")
                return []

            # ***Correctly filter predefined locations***
            filtered_locations = {place: details for place, details in famous_indian_locations.items() if details['Category'].lower() == category.lower()} if category else famous_indian_locations
            
            if filtered_locations:
                response = ""
                if country and category:
                    response += f"Here are some {category} destinations in India:\n"
                elif category:
                    response += f"Here are some {category} destinations:\n"
                else:
                    response += f"Here are some destinations in India:\n"
                    
                for place, details in filtered_locations.items():
                    response += f"- {place}\n"
                dispatcher.utter_message(text=response)
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find any {category} destinations in India.")
            return []  # Very Important: Return here!

        else:  # Use CSV data
            # ... (CSV data handling logic - this part is correct from previous responses)
            if category and category.lower() not in valid_categories:
                dispatcher.utter_message(text=f"Sorry, '{category}' is not a valid category. Available categories are: {', '.join(sorted(valid_categories)) or 'None'}.")
                return []

            if country and country.lower() not in valid_countries:
                dispatcher.utter_message(text=f"Sorry, '{country}' is not a valid country. Available countries are: {', '.join(sorted(valid_countries)) or 'None'}.")
                return []

            filtered_df = df.copy()

            if country:
                filtered_df = filtered_df[filtered_df["Country"].str.lower() == country.lower()]
            if category:
                filtered_df = filtered_df[filtered_df["Category"].str.lower() == category.lower()]

            if not filtered_df.empty:
                response = ""
                if country and category:
                    response += f"Here are some {category} destinations in {country}:\n"
                elif category:
                    response += f"Here are some {category} destinations:\n"
                elif country:
                    response += f"Here are some destinations in {country}:\n"

                locations = set()  # Use a set to avoid duplicates
                for index, row in filtered_df.iterrows():
                    location_parts = []
                    if 'Place' in row and row['Place']: #Check if Place exists and is not empty
                        location_parts.append(row['Place'])
                    else:
                        if 'Country' in row and row['Country']:
                            location_parts.append(row['Country'])
                        if 'Category' in row and row['Category']:
                            location_parts.append(row['Category'])
                    location = ", ".join(location_parts)
                    if location:
                        locations.add(location)

                for location in sorted(locations):
                    response += f"- {location}\n"

                dispatcher.utter_message(text=response)
            else:
                message = "Sorry, I couldn't find any destinations"
                if country and category:
                    message += f" for {category} in {country}."
                elif category:
                    message += f" for {category}."
                elif country:
                    message += f" in {country}."
                dispatcher.utter_message(text=message)
            return []


class ActionProvideTourismByCountry(Action):
    def name(self) -> Text:
        return "action_provide_tourism_by_country"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        tracker.slots["category"] = None
        return ActionProvideTourismByCategory().run(dispatcher, tracker, domain)

class ActionProvideTourismByRating(Action):
    def name(self) -> Text:
        return "action_provide_tourism_by_rating"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        print("Inside action_provide_tourism_by_rating")
        if df.empty:
            dispatcher.utter_message(text="Data file not loaded. Cannot provide tourism information.")
            return []

        try:
            df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
            df_filtered = df.dropna(subset=['Rating']).copy()

            if df_filtered.empty:
                dispatcher.utter_message(text="No valid rating values found in the dataset.")
                return []

            if 'Country' not in df_filtered.columns:  # Check if 'Country' is present
                dispatcher.utter_message(text="The 'Country' column is missing after filtering. Please check your data.")
                print("Columns after filtering:", df_filtered.columns)
                return []

            df_sorted = df_filtered.sort_values(by='Rating', ascending=False).reset_index(drop=True)
            top_n = 5
            top_destinations = df_sorted.head(top_n)

            if not top_destinations.empty:
                response = f"Here are the top {top_n} destinations based on ratings:\n"
                for index, row in top_destinations.iterrows():
                    response += f"- {row['Country']} - Rating: {row['Rating']}\n"  # Use 'Country' instead of 'Location'
                dispatcher.utter_message(text=response)
            else:
                dispatcher.utter_message(text="No destinations found with ratings in the dataset.")

        except KeyError as e:
            dispatcher.utter_message(text=f"A KeyError occurred: {e}. Please check your dataset and column names.")
            print(f"KeyError details: {e}")
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while processing ratings: {e}")
            print(f"Other Error details: {e}")

        return []
    
class ActionProvideTopRatedPlacesInIndia(Action): #New Action
    def name(self) -> Text:
        return "action_provide_top_rated_places_in_india"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # This action ONLY handles the predefined locations
        sorted_locations = sorted(famous_indian_locations.items(), key=lambda item: item[1]['Rating'], reverse=True)
        response = "Here are the top-rated destinations in India:\n"
        for place, details in sorted_locations:
            response += f"- {place}\n"
        dispatcher.utter_message(text=response)
        return []

class ActionCheckAccommodation(Action):
    def name(self) -> Text:
        return "action_check_accommodation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        country = tracker.get_slot("country")
        category = tracker.get_slot("category")

        if df.empty:
            dispatcher.utter_message(
                text=
                "Data file not loaded. Cannot provide accommodation information."
            )
            return []

        if country:
            country = country.lower()
            if country not in valid_countries:
                dispatcher.utter_message(
                    text=
                    f"Sorry, '{country}' is not a valid country. Available countries are: {', '.join(sorted(valid_countries)) or 'No countries available in the dataset'}."
                )
                return []

        if category:
            category = category.lower()
            if category not in valid_categories:
                dispatcher.utter_message(
                    text=
                    f"Sorry, '{category}' is not a valid category. Available categories are: {', '.join(sorted(valid_categories)) or 'No categories available in the dataset'}."
                )
                return []

        filtered_df = df.copy()  # Create a copy to avoid modifying the original df

        if country:
            filtered_df = filtered_df[
                filtered_df["Country"].str.lower() == country]
        if category:
            filtered_df = filtered_df[
                filtered_df["Category"].str.lower() == category]

        # Filter for accommodation availability *after* filtering by country and category
        available_accommodations = filtered_df[
            filtered_df["Accommodation_Available"].str.lower() == "yes"]

        if not available_accommodations.empty:
            message_prefix = "Yes, accommodations are available"
            if country and category:
                message_prefix += f" for {category} tourism in {country}."
            elif country:
                message_prefix += f" in {country}."
            elif category:
                message_prefix += f" for {category} tourism."
            dispatcher.utter_message(text=message_prefix)

            # (Optional) Display additional information for available accommodations
            for index, row in available_accommodations.iterrows():
                message = "- "
                if "Rating" in row:
                    message += f"Rating: {row['Rating']}, "
                if "Category" in row:
                    message += f"Category: {row['Category']}, "
                if "Country" in row:
                    message += f"Country: {row['Country']}"
                dispatcher.utter_message(text=message)
        else:
            message = "Sorry, there are no accommodations available"
            if country and category:
                message += f" for {category} tourism in {country}."
            elif country:
                message += f" in {country}."
            elif category:
                message += f" for {category} tourism."
            dispatcher.utter_message(text=message)

        return []
