import React, { useState, useCallback, useRef, useEffect } from 'react';
import type { Location, SearchResult } from '../types';
import { LocationSearchService } from '../services/locationSearchService';
import { MAP_CONFIG } from '../constants';

interface LocationSearchProps {
  onLocationSelect: (location: Location) => void;
  placeholder?: string;
}

export const LocationSearch: React.FC<LocationSearchProps> = ({
  onLocationSelect,
  placeholder = "Search for a location..."
}) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const searchService = LocationSearchService.getInstance();
  const debounceRef = useRef<NodeJS.Timeout | undefined>(undefined);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }

    setIsLoading(true);
    try {
      const searchResults = await searchService.searchLocations(searchQuery);
      setResults(searchResults);
      setShowDropdown(searchResults.length > 0);
      setSelectedIndex(-1);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
      setShowDropdown(false);
    } finally {
      setIsLoading(false);
    }
  }, [searchService]);

  const debouncedSearch = useCallback((searchQuery: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      performSearch(searchQuery);
    }, MAP_CONFIG.searchDebounceMs);
  }, [performSearch]);

  const handleClearSearch = () => {
    setQuery('');
    setResults([]);
    setShowDropdown(false);
    setSelectedIndex(-1);
    inputRef.current?.focus();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };

  const handleResultSelect = (result: SearchResult) => {
    const location = searchService.convertSearchResultToLocation(result);
    onLocationSelect(location);
    setQuery(result.display_name);
    setShowDropdown(false);
    setSelectedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : prev);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleResultSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowDropdown(false);
        setSelectedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  const handleInputBlur = () => {
    // Delay hiding dropdown to allow click events on results
    setTimeout(() => {
      setShowDropdown(false);
      setSelectedIndex(-1);
    }, 200);
  };

  const handleInputFocus = () => {
    if (results.length > 0) {
      setShowDropdown(true);
    }
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  return (
    <div className="location-search">
      <div className="search-input-container">
        <div className="search-icon">
          🔍
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onBlur={handleInputBlur}
          onFocus={handleInputFocus}
          placeholder={placeholder}
          className="search-input"
          autoComplete="off"
        />
        {query && (
          <button
            type="button"
            onClick={handleClearSearch}
            className={`search-clear-button ${query ? 'visible' : ''}`}
            aria-label="Clear search"
          >
            ✕
          </button>
        )}
        {isLoading && (
          <div className="search-loading-spinner"></div>
        )}
      </div>

      {showDropdown && (
        <div ref={dropdownRef} className="search-results">
          {isLoading ? (
            <div className="search-loading">
              <div className="search-loading-spinner"></div>
              Searching...
            </div>
          ) : results.length > 0 ? (
            results.map((result, index) => (
              <div
                key={result.place_id}
                className={`search-result-item ${index === selectedIndex ? 'selected' : ''}`}
                onClick={() => handleResultSelect(result)}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="search-result-icon">
                  📍
                </div>
                <div className="search-result-text">
                  {result.display_name}
                </div>
              </div>
            ))
          ) : query && !isLoading ? (
            <div className="search-empty">
              <div className="search-empty-icon">🔍</div>
              No locations found for "{query}"
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
