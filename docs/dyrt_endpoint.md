# TheDyrt API Endpoint Documentation

## Overview

This document provides usage details for the TheDyrt location search-results API endpoint (`/api/v6/locations/search-results`). This endpoint returns campground metadata (latitude, longitude, name, rating, photos, etc.) in JSON format, which can be validated against our Pydantic `Campground` model and stored in PostgreSQL.

---

## Base URL

```
https://thedyrt.com/api/v6/locations/search-results
```

All requests are made via HTTP GET.

---

## Query Parameters

The endpoint supports the following query parameters for filtering, pagination, and sorting:

| Parameter                            | Description                                                                   | Example Value                |
| ------------------------------------ | ----------------------------------------------------------------------------- | ---------------------------- |
| `filter[search][drive_time]`         | Filter by maximum driving time                                                | `any`                        |
| `filter[search][air_quality]`        | Filter by air quality rating                                                  | `any`                        |
| `filter[search][electric_amperage]`  | Filter by available electric amperage                                         | `any`                        |
| `filter[search][max_vehicle_length]` | Filter by maximum vehicle length (feet)                                       | `any`                        |
| `filter[search][price]`              | Filter by price range                                                         | `any`                        |
| `filter[search][rating]`             | Filter by campground rating                                                   | `any`                        |
| `filter[search][bbox]`               | Bounding box `west_lon,south_lat,east_lon,north_lat` to limit geographic area | `-124.84,24.39,-66.88,49.38` |
| `sort`                               | Sort order, e.g., `recommended`                                               | `recommended`                |
| `page[number]`                       | Page number (1-based)                                                         | `1`                          |
| `page[size]`                         | Number of records per page (max \~500)                                        | `500`                        |

> Note: All square-bracket parameters are percent-encoded in the actual URL, e.g., `filter%5Bsearch%5D%5Bdrive_time%5D=any`.

---

## Example Request

```bash
curl -X GET "https://thedyrt.com/api/v6/locations/search-results?\
  filter[search][drive_time]=any&\
  filter[search][air_quality]=any&\
  filter[search][electric_amperage]=any&\
  filter[search][max_vehicle_length]=any&\
  filter[search][price]=any&\
  filter[search][rating]=any&\
  filter[search][bbox]=-124.84,24.39,-66.88,49.38&\
  sort=recommended&\
  page[number]=1&\
  page[size]=500"
```

---

## Response Structure

The endpoint returns a JSON object with the following top-level keys:

* `data`: List of location records
* `meta`: Pagination metadata (`total`, `pageSize`, `pageNumber`, etc.)

### `data` Item Schema

Each item in `data` contains:

```json
{
  "id": "<string>",               // Unique global ID (base64)
  "type": "location-search-results",
  "links": {"self": "<url>"},
  "attributes": {
    "name": "<string>",
    "latitude": <float>,
    "longitude": <float>,
    "region-name": "<string>",
    "administrative-area": "<string> (optional)",
    "nearest-city-name": "<string> (optional)",
    "accommodation-type-names": [<string>, ...],
    "bookable": <bool>,
    "camper-types": [<string>, ...],
    "operator": "<string> (optional)",
    "photo-url": "<url> (optional)",
    "photo-urls": [<url>, ...],
    "photos-count": <int>,
    "rating": <float> (optional),
    "reviews-count": <int>,
    "slug": "<string> (optional)",
    "price-low": "<string> (decimal)",
    "price-high": "<string> (decimal)",
    "availability-updated-at": "<ISO8601 datetime>"
    // ... other attributes
  }
}
```

These fields map directly to our Pydantic `Campground` model, with aliases:

```python
Campground(
    id=item.id,
    type=item.type,
    links=CampgroundLinks(self=item.links.self),
    name=attr["name"],
    latitude=attr["latitude"],
    longitude=attr["longitude"],
    region_name=attr["region-name"],
    administrative_area=attr.get("administrative-area"),
    nearest_city_name=attr.get("nearest-city-name"),
    accommodation_type_names=attr.get("accommodation-type-names", []),
    bookable=attr.get("bookable", False),
    camper_types=attr.get("camper-types", []),
    operator=attr.get("operator"),
    photo_url=attr.get("photo-url"),
    photo_urls=attr.get("photo-urls", []),
    photos_count=attr.get("photos-count", 0),
    rating=attr.get("rating"),
    reviews_count=attr.get("reviews-count", 0),
    slug=attr.get("slug"),
    price_low=float(attr.get("price-low", 0)),
    price_high=float(attr.get("price-high", 0)),
    availability_updated_at=attr.get("availability-updated-at")
)
```

---
