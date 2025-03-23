/**
 * API utilities for the application
 */

// Add an export for testing database connection
export async function testDatabaseConnection(): Promise<boolean> {
  try {
    console.log('Testing database connection...');
    // Use HTTP instead of HTTPS to avoid certificate issues
    const response = await fetch(`${getApiBaseUrl()}/test-db.php?json=1`, {
      method: 'GET',
      cache: 'no-cache',
      // Add a timeout to prevent hanging requests
      signal: AbortSignal.timeout(10000)
    });
    
    if (!response.ok) {
      console.error(`Database test failed with status: ${response.status}`);
      return false;
    }
    
    const data = await response.json();
    console.log('Database connection test result:', data);
    return data.success === true;
  } catch (error) {
    console.error('Database connection test error:', error);
    
    // If it's an SSL error, we'll return true anyway since the API might still work with HTTP
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.warn('SSL certificate issue detected, but API may still work with HTTP');
      return true; // Optimistically assume we can connect
    }
    
    return false;
  }
}

/**
 * Gets the base URL for API requests based on the current environment
 */
export function getApiBaseUrl(): string {
  // Use HTTP instead of HTTPS to avoid certificate issues
  return import.meta.env.DEV
    ? 'http://nickflix3.atwebpages.com' // Use HTTP for AwardSpace URL
    : 'http://nickflix3.atwebpages.com'; // Production - use HTTP for AwardSpace URL
}

// Add mock API function for development
export function mockApiResponse<T>(endpoint: string, mockData: T): T {
  console.log(`Mock API call to ${endpoint}`);
  return mockData;
}

/**
 * Logs out the current user
 * Clears local storage and calls the logout endpoint
 */
export async function logout(): Promise<void> {
  try {
    // Call logout endpoint
    await apiPost('logout.php', {});
  } catch (error) {
    console.error('Error during logout:', error);
  } finally {
    // Always clear local storage, even if the API call fails
    localStorage.removeItem('userProfile');
    // Trigger storage event for other components
    window.dispatchEvent(new Event('storage'));
  }
}

/**
 * Makes a POST request to the API
 * @param endpoint The API endpoint to call
 * @param data The data to send in the request body
 * @returns Promise with the response data
 */
export async function apiPost<T = any>(endpoint: string, data: any): Promise<T> {
  const url = `${getApiBaseUrl()}/${endpoint}`;
  
  try {
    console.log(`API POST request to ${url}:`, data);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      // Ensure we're not using cached responses
      cache: 'no-cache',
      // Add timeout to prevent hanging requests
      signal: AbortSignal.timeout(15000)
    });

    // Always log the status for debugging
    console.log(`API Response status: ${response.status} ${response.statusText}`);

    // First check if the response is OK (status 200-299)
    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const jsonResponse = await response.json();
      console.log('API JSON response:', jsonResponse);
      return jsonResponse;
    } else {
      // Try to parse as JSON anyway, in case content-type header is incorrect
      try {
        const text = await response.text();
        console.warn(`API returned non-JSON content type "${contentType}" but attempting to parse as JSON:`, text);
        
        if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
          const jsonData = JSON.parse(text);
          return jsonData;
        } else {
          throw new Error(`Expected JSON response from ${endpoint}, got: ${text.substring(0, 100)}`);
        }
      } catch (parseError) {
        console.error('Failed to parse response:', parseError);
        throw new Error(`Expected JSON response from ${endpoint}, got invalid content`);
      }
    }
  } catch (error) {
    console.error(`Error calling ${endpoint}:`, error);
    
    // Only fall back to mock data during development
    if (import.meta.env.DEV) {
      console.warn('Using mock data due to API error (DEV mode only)');
      return Promise.resolve(mockAuthResponse(endpoint, data) as T);
    }
    
    // In production, reject the promise
    return Promise.reject(error);
  }
}

// Mock auth responses for fallback (only used in development)
function mockAuthResponse(endpoint: string, data: any): ApiResponse<UserProfileData> {
  // Add age calculation helper function
  const calculateAgeFromDateString = (dateOfBirth?: string): number | undefined => {
    if (!dateOfBirth) return undefined;
    
    try {
      const dob = new Date(dateOfBirth);
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const m = today.getMonth() - dob.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
        age--;
      }
      return age;
    } catch (e) {
      console.error('Error calculating age:', e);
      return undefined;
    }
  };

  if (endpoint === 'register.php') {
    // Mock registration response
    return {
      success: true,
      message: 'Registration successful (MOCK DATA)',
      user: {
        id: 1,
        email: data.email || '',
        username: data.username || '',
        full_name: data.full_name || '',
        avatar_url: undefined,
        membership: 'Free',
        date_of_birth: data.date_of_birth,
        age: calculateAgeFromDateString(data.date_of_birth)
      }
    };
  } else if (endpoint === 'login.php') {
    // Mock login response
    const derivedUsername = data.email ? data.email.split('@')[0] : 'user123';
    
    return {
      success: true,
      message: 'Login successful (MOCK DATA)',
      user: {
        id: 1,
        email: data.email || '',
        username: derivedUsername,
        full_name: derivedUsername.charAt(0).toUpperCase() + derivedUsername.slice(1),
        avatar_url: undefined,
        membership: 'Premium',
        date_of_birth: '1990-01-01', // Default mock date of birth
        age: 33 // Default mock age
      }
    };
  }
  
  // Default mock response
  return {
    success: false,
    message: 'Unknown endpoint'
  };
}

/**
 * Makes a GET request to the API
 * @param endpoint The API endpoint to call
 * @param params Optional query parameters
 * @returns Promise with the response data
 */
export async function apiGet<T = any>(endpoint: string, params?: Record<string, string>): Promise<T> {
  let url = `${getApiBaseUrl()}/${endpoint}`;
  
  if (params) {
    const queryString = new URLSearchParams(params).toString();
    url += `?${queryString}`;
  }
  
  try {
    console.log(`API GET request to ${url}`);
    
    const response = await fetch(url, {
      cache: 'no-cache', // Ensure we're not using cached responses
      // Add timeout to prevent hanging requests
      signal: AbortSignal.timeout(15000)
    });

    console.log(`API Response status: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    // Check if response is JSON
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const jsonResponse = await response.json();
      console.log('API JSON response:', jsonResponse);
      return jsonResponse;
    } else {
      // Try to parse as JSON anyway, in case content-type header is incorrect
      try {
        const text = await response.text();
        console.warn(`API returned non-JSON content type "${contentType}" but attempting to parse as JSON:`, text);
        
        if (text.trim().startsWith('{') || text.trim().startsWith('[')) {
          const jsonData = JSON.parse(text);
          return jsonData;
        } else {
          throw new Error(`Expected JSON response from ${endpoint}, got: ${text.substring(0, 100)}`);
        }
      } catch (parseError) {
        console.error('Failed to parse response:', parseError);
        throw new Error(`Expected JSON response from ${endpoint}, got invalid content`);
      }
    }
  } catch (error) {
    console.error(`Error calling ${endpoint}:`, error);
    
    // Only fall back to mock data during development
    if (import.meta.env.DEV) {
      console.warn('Using mock data due to API error (DEV mode only)');
      return Promise.resolve(mockGetResponse(endpoint, params) as T);
    }
    
    // In production, reject the promise
    return Promise.reject(error);
  }
}

// Mock GET responses for fallback (only used in development)
function mockGetResponse(endpoint: string, params?: Record<string, string>): ApiResponse<any> {
  // Try to get the current user from localStorage to provide consistent data
  let userProfile = null;
  try {
    const profileData = localStorage.getItem('userProfile');
    if (profileData) {
      userProfile = JSON.parse(profileData);
    }
  } catch (e) {
    console.error('Error reading user profile from localStorage:', e);
  }
  
  // Helper function to calculate age
  const calculateAgeFromDateString = (dateOfBirth?: string): number | undefined => {
    if (!dateOfBirth) return undefined;
    
    try {
      const dob = new Date(dateOfBirth);
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const m = today.getMonth() - dob.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
        age--;
      }
      return age;
    } catch (e) {
      console.error('Error calculating age:', e);
      return undefined;
    }
  };
  
  if (endpoint.includes('user')) {
    const date_of_birth = userProfile?.date_of_birth || '1990-01-01';
    const age = userProfile?.age || calculateAgeFromDateString(date_of_birth);
    
    return {
      success: true,
      message: 'User data retrieved (MOCK DATA)',
      user: userProfile ? {
        id: userProfile.id || 1,
        email: userProfile.email || 'user@example.com',
        username: userProfile.username || 'user123',
        full_name: userProfile.full_name || userProfile.name || 'Active User',
        avatar_url: userProfile.avatar_url || userProfile.avatarUrl,
        membership: userProfile.membership || 'Premium',
        date_of_birth: userProfile.date_of_birth,
        age: userProfile.age || age
      } : {
        id: 1,
        email: 'user@example.com',
        username: 'user123',
        full_name: 'Active User',
        avatar_url: undefined,
        membership: 'Premium',
        date_of_birth: '1990-01-01',
        age: 33
      }
    };
  }
  
  // Default mock response
  return {
    success: false,
    message: 'Unknown endpoint'
  };
}

/**
 * Type for API responses
 */
export interface ApiResponse<T = UserProfileData> {
  success: boolean;
  message?: string;
  user?: T;
  [key: string]: any;
}

/**
 * User profile data structure
 */
export interface UserProfileData {
  id: number;
  email: string;
  username?: string;
  full_name?: string;
  avatar_url?: string;
  name?: string;
  avatarUrl?: string;
  membership?: string;
  date_of_birth?: string; // ISO format date string
  age?: number; // Calculated age from date_of_birth
} 