import { FC } from 'react';

export const UnderConstruction: FC = () => {
  return (
    <div className="min-h-screen bg-bg-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-text-100 mb-4">Under Construction</h1>
        <p className="text-text-200">This page is currently under development. Please check back later.</p>
      </div>
    </div>
  );
}; 