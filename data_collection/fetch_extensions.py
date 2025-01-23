import requests
import json
 
 

def fetch_vscode_extensions(search_terms, max_results):
    """
    Fetch VSCode extensions based on a list of search terms and extract specific data 
    (publisher_name, ext_name, link_to_extension, downloads, ratings, trends, and install stats).
    
    Args:
        search_terms (list): List of search terms to query extensions.
        max_results (int): Maximum number of extensions to fetch per term.
    
    Returns:
        list: List of dictionaries containing publisher_name, ext_name, link_to_extension,
              and statistics such as downloads, average_rating, rating_count, and trending values.
    """
    url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json;api-version=3.0-preview.1"
    }

    page_size = 50  # API allows up to 50 extensions per page
    all_results = []

    for term in search_terms:
        term = term.strip()
        if not term:
            term = ""

        page_number = 1
        results = []

        while len(results) < max_results:
            payload = {
                "filters": [{
                    "criteria": [{"filterType": 10, "value": term}],
                    "pageNumber": page_number,
                    "pageSize": page_size,
                    "sortBy": 0,
                    "sortOrder": 0
                }],
                "flags": 914
            }

            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                data = response.json()
                extensions = data.get("results", [])[0].get("extensions", [])
                if not extensions:
                    break
                results.extend(extensions)
                page_number += 1
            else:
                break

        # Limit results per term to max_results
        results = results[:max_results]
        for ext in results:
            ext["Search Term"] = term  # Add search term for grouping later
        all_results.extend(results)

    if not all_results:
        return []

    # Extract only the required data: publisher_name, ext_name, and link_to_extension
    extensions_data = []
    for ext in all_results:
        publisher_name = ext["publisher"].get("publisherName", "N/A") if "publisher" in ext else "N/A"
        ext_name = ext.get("extensionName", "N/A")

        # Build the direct link to the Marketplace
        link_to_extension = f"https://marketplace.visualstudio.com/items?itemName={publisher_name}.{ext_name}"

        # Extract statistics
        downloads = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "install"), 0)
        avg_rating = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "averagerating"), 0)
        rating_count = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "ratingcount"), 0)
        update_count = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "updateCount"), 0)
        trending_daily = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "trendingdaily"), 0)
        trending_weekly = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "trendingweekly"), 0)
        trending_monthly = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "trendingmonthly"), 0)
        trending_overall = next((stat["value"] for stat in ext["statistics"] if stat["statisticName"] == "trendingOverall"), 0)

        # Append the collected data
        extensions_data.append({
            "publisher_name": publisher_name,  # Name of the publisher of the extension
            "ext_name": ext_name,  # Name of the extension
            "link_to_extension": link_to_extension,  # Direct link to the Marketplace page
            "downloads": int(downloads),  # Total number of installs (download count)
            "average_rating": avg_rating,  # Average user rating
            "rating_count": rating_count,  # Total number of ratings
            "update_count": update_count,  # Number of updates for the extension
            "trending_daily": trending_daily,  # Daily trending value
            "trending_weekly": trending_weekly,  # Weekly trending value
            "trending_monthly": trending_monthly,  # Monthly trending value
            "trending_overall": trending_overall  # Overall trending score
        })

    return extensions_data










def save_to_json(data, file_path):
    """
    Save the fetched VSCode extensions data to a JSON file.
    
    Args:
        data (dict): Dictionary containing extensions data.
        file_path (str): Path to the JSON file to create.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Data successfully saved to {file_path}")
    except Exception as e:
        print(f"Error saving data to JSON: {e}")

