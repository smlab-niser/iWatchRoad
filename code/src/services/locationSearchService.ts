import type { SearchResult, Location } from '../types';
import { NOMINATIM_BASE_URL } from '../constants';

export class LocationSearchService {
  private static instance: LocationSearchService;

  static getInstance(): LocationSearchService {
    if (!LocationSearchService.instance) {
      LocationSearchService.instance = new LocationSearchService();
    }
    return LocationSearchService.instance;
  }

  async searchLocations(query: string, limit: number = 5): Promise<SearchResult[]> {
    if (!query.trim()) {
      return [];
    }

    try {
      const params = new URLSearchParams({
        q: query,
        format: 'json',
        limit: limit.toString(),
        addressdetails: '1',
        countrycodes: 'in', // Focus on India but allow global search
      });

      const response = await fetch(`${NOMINATIM_BASE_URL}?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: SearchResult[] = await response.json();
      return data;
    } catch (error) {
      console.error('Error searching locations:', error);
      return [];
    }
  }

  convertSearchResultToLocation(result: SearchResult): Location {
    return {
      lat: parseFloat(result.lat),
      lng: parseFloat(result.lon),
      name: result.display_name
    };
  }
}
