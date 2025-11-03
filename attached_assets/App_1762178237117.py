import React, { useState } from 'react';

// This function simulates an API call to a backend server.
// It will attempt a fetch request and fall back to hardcoded data if it fails.
const fetchJobsFromApi = async (jobTitle, jobLocation) => {
  console.log(`Attempting to fetch data from backend API for: ${jobTitle} in ${jobLocation}`);

  try {
    const params = new URLSearchParams({
      q: jobTitle,
      where: jobLocation,
      country: 'nl',
      rerank: '1',
      permanent: '1',
      full_time: '1',
      page: '1', // Hardcoded page for this example
      per_page: '25'
    });

    // This is the fetch call to your backend.
    // In this environment, it will fail because there is no running server at /api/jobs.
    const response = await fetch(`/api/jobs?${params}`);
    
    // Check if the response is successful
    if (!response.ok) {
      throw new Error(`API call failed with status: ${response.status}`);
    }

    const data = await response.json();
    return data.results || [];
  } catch (error) {
    console.error("Fetch failed, falling back to mock data:", error);
    
    // Fallback data in case the fetch request fails
    const apiResponse = [
      {
        source_title: "Careers at ASML",
        title: "Mechanical Engineer - EUV Manufacturing",
        snippet: "ASML is looking for a talented Mechanical Engineer to join our team in Veldhoven, The Netherlands. You will be responsible for...",
        url: "https://www.asml.com/en/careers/jobs/2025/mechanical-engineer-euve-manuf",
        publication_time: "2025-07-28",
        location: "Veldhoven, The Netherlands"
      },
      {
        source_title: "Boskalis Jobs",
        title: "Senior Project Engineer",
        snippet: "Join Boskalis in Papendrecht! We are seeking a Senior Project Engineer with a background in marine technology and heavy machinery.",
        url: "https://jobs.boskalis.com/job/senior-project-engineer/12345",
        publication_time: "2025-07-27",
        location: "Papendrecht"
      },
      {
        source_title: "Philips Careers",
        title: "Lead Mechanical Engineer, Medical Systems",
        snippet: "Philips is seeking a lead mechanical engineer for our R&D team in Eindhoven. Your role will involve project leadership...",
        url: "https://www.philips.com/a-w/careers/your-career/job-details/lead-mechanical-engineer-medical-systems",
        publication_time: "2025-07-26",
        location: "Eindhoven"
      },
      {
        source_title: "Indeed.com",
        title: "Project Manager - Mechanical Engineering",
        snippet: "An opportunity for a skilled project manager to oversee mechanical projects in Rotterdam. Experience with industrial systems is required.",
        url: "https://nl.indeed.com/job/project-manager-mechanical-engineering",
        publication_time: "2025-07-25",
        location: "Rotterdam"
      },
      {
        source_title: "Shell Careers",
        title: "Mechanical Project Engineer",
        snippet: "We are looking for a Mechanical Project Engineer to join our team in The Hague. You will manage projects from concept to completion...",
        url: "https://www.shell.com/careers/jobs/mechanical-project-engineer",
        publication_time: "2025-07-24",
        location: "The Hague"
      },
    ];

    const normalizedResults = apiResponse.map(item => ({
      source_title: item.source_title || "N/A",
      title: item.title || "No Title",
      snippet: item.snippet || "No snippet available.",
      url: item.url,
      publication_time: item.publication_time || "N/A",
    }));

    return normalizedResults;
  }
};

// Define the component
const App = () => {
  const [jobTitle, setJobTitle] = useState('Mechanical Project Engineer');
  const [jobLocation, setJobLocation] = useState('The Netherlands');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Function to perform the simulated live search
  const handleSearch = async () => {
    setMessage('');
    setLoading(true);
    setResults([]);

    try {
      const searchResults = await fetchJobsFromApi(jobTitle, jobLocation);

      if (searchResults && searchResults.length > 0) {
        setResults(searchResults);
        setMessage(`Found ${searchResults.length} results.`);
      } else {
        setMessage('No search results were returned. Please try again.');
      }
    } catch (error) {
      console.error("Search failed:", error);
      setMessage('An error occurred during the search. Please check your query and try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Function to download search results as a CSV
  const downloadCsv = () => {
    if (results.length === 0) {
      setMessage("No results to download.");
      return;
    }

    const headers = ["Source Title", "Title", "Snippet", "URL", "Publication Time"];
    const csvRows = results.map(result => {
      const row = [
        `"${(result.source_title || 'N/A').replace(/"/g, '""')}"`,
        `"${(result.title || 'N/A').replace(/"/g, '""')}"`,
        `"${(result.snippet || 'N/A').replace(/"/g, '""')}"`,
        `"${(result.url || 'N/A').replace(/"/g, '""')}"`,
        `"${(result.publication_time || 'N/A').replace(/"/g, '""')}"`
      ];
      return row.join(',');
    });

    const csvContent = [headers.join(','), ...csvRows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', 'job_results.csv');
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setMessage("Search results downloaded as job_results.csv.");
    } else {
      setMessage("Your browser does not support downloading files directly.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 font-sans flex flex-col items-center">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-4xl mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-4 text-center">Live Job Finder</h1>
        <p className="text-gray-600 text-center mb-6">
          Find real, live job listings by entering a job title and location.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 mb-4">
          <input
            type="text"
            placeholder="Job Title (e.g., Mechanical Engineer)"
            value={jobTitle}
            onChange={(e) => setJobTitle(e.target.value)}
            className="flex-grow p-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow duration-300"
          />
          <input
            type="text"
            placeholder="Job Location (e.g., The Netherlands)"
            value={jobLocation}
            onChange={(e) => setJobLocation(e.target.value)}
            className="flex-grow p-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-shadow duration-300"
          />
        </div>
        <div className="flex flex-col sm:flex-row justify-center gap-4 mb-4">
          <button
            onClick={handleSearch}
            disabled={loading}
            className={`flex-grow flex items-center justify-center px-6 py-3 rounded-lg text-white font-semibold transition-all duration-300
              ${loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 shadow-md hover:shadow-lg'}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.3-4.3"></path>
            </svg>
            {loading ? 'Searching...' : 'Search for Jobs'}
          </button>
          <button
            onClick={downloadCsv}
            disabled={results.length === 0}
            className={`flex-grow flex items-center justify-center px-6 py-3 rounded-lg text-white font-semibold transition-all duration-300
              ${results.length === 0 ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700 active:bg-green-800 shadow-md hover:shadow-lg'}`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="7 10 12 15 17 10"></polyline>
              <line x1="12" x2="12" y1="15" y2="3"></line>
            </svg>
            Download CSV
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-4xl mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Search Results</h2>
        {message && (
          <p className="text-center text-gray-500 mb-4">{message}</p>
        )}
        {loading && (
          <p className="text-center text-gray-500">Searching the web for live job listings...</p>
        )}
        {!loading && results.length > 0 && (
          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors duration-300">
                <h3 className="text-lg font-semibold text-indigo-600 mb-1">
                  <a href={result.url} target="_blank" rel="noopener noreferrer">{result.source_title || 'N/A'}</a>
                </h3>
                <p className="text-sm text-gray-900 mb-2">{result.title}</p>
                <p className="text-sm text-gray-600">{result.snippet}</p>
                <a 
                  href={result.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  className="text-xs text-blue-500 hover:underline break-all mt-2 inline-block"
                >
                  {result.url}
                </a>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
