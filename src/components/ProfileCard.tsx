import React from "react";
import { UserProfileData } from "@/lib/api";
import { calculateAge } from "./ui/DatePicker";

interface ProfileCardProps {
  /**
   * The full name of the user
   */
  name: string;
  
  /**
   * The email address of the user
   */
  email: string;
  
  /**
   * The URL to the user's avatar image
   * If not provided, initials will be used as fallback
   */
  avatarUrl?: string;
  
  /**
   * The membership tier of the user
   */
  membership: string;
  
  /**
   * The user's date of birth (optional)
   */
  dateOfBirth?: string;
  
  /**
   * The user's age (optional)
   */
  age?: number;
  
  /**
   * Optional CSS class names
   */
  className?: string;
}

/**
 * Get the current user profile from localStorage
 * @returns The user profile or null if not found
 */
export function getCurrentUserProfile(): UserProfileData | null {
  try {
    const profileData = localStorage.getItem('userProfile');
    if (!profileData) return null;
    
    const profile = JSON.parse(profileData);
    
    // Calculate age from date of birth if age is not already provided
    let age = profile.age;
    if (profile.date_of_birth && !age) {
      const dob = new Date(profile.date_of_birth);
      age = calculateAge(dob);
    }
    
    return {
      id: profile.id,
      name: profile.name || profile.full_name || profile.username || 'Guest User',
      email: profile.email || '',
      avatarUrl: profile.avatarUrl || profile.avatar_url || undefined,
      membership: profile.membership || 'Free',
      username: profile.username,
      full_name: profile.full_name,
      avatar_url: profile.avatar_url,
      date_of_birth: profile.date_of_birth,
      age: age
    };
  } catch (error) {
    console.error('Error getting user profile:', error);
    return null;
  }
}

/**
 * A profile card component that displays user information
 */
export function ProfileCard({ 
  name, 
  email, 
  avatarUrl, 
  membership, 
  dateOfBirth, 
  age,
  className 
}: ProfileCardProps) {
  // Calculate initials from name for avatar fallback
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  // Calculate age from date of birth if age is not provided
  let displayAge = age;
  if (dateOfBirth && !displayAge) {
    const dob = new Date(dateOfBirth);
    displayAge = calculateAge(dob);
  }

  return (
    <div className={`p-4 border-b border-primary-200/20 ${className || ""}`}>
      <div className="flex items-center gap-3">
        {avatarUrl ? (
          <div className="w-10 h-10 rounded-full overflow-hidden">
            <img src={avatarUrl} alt={name} className="w-full h-full object-cover" />
          </div>
        ) : (
          <div className="w-10 h-10 rounded-full bg-accent-200 flex items-center justify-center text-white font-medium">
            {initials}
          </div>
        )}
        <div className="flex-1">
          <div className="font-medium text-text-100">{name}</div>
          <div className="text-xs text-text-200">{email}</div>
          <div className="mt-1 flex flex-wrap gap-1">
            <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-bg-200/80 text-text-100">
              {membership}
            </span>
            {displayAge && (
              <span className="inline-block text-xs px-2 py-0.5 rounded-full bg-accent-100/30 text-accent-200">
                {displayAge} years old
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 