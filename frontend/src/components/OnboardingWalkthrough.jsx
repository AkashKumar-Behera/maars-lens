import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const OnboardingWalkthrough = ({ role }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem(`onboarding_${role}`);
    if (!completed) {
      setIsVisible(true);
    }
  }, [role]);

  const handleDismiss = () => {
    setIsVisible(false);
    localStorage.setItem(`onboarding_${role}`, 'true');
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-indigo-900 bg-opacity-75 z-[60] flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full p-6 relative">
        <button onClick={handleDismiss} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <X size={24} />
        </button>
        <h2 className="text-2xl font-bold text-indigo-600 mb-4">Welcome to MAARS Lens</h2>
        <div className="space-y-4 mb-6">
          <p className="text-gray-700">Let's get you started. Here's what you can do:</p>
          {role === 'officer' && (
            <ul className="list-disc pl-5 text-sm text-gray-600 space-y-2">
              <li><strong>Dashboard:</strong> View your stats and pending tasks.</li>
              <li><strong>New Scan:</strong> Use your camera to capture product labels for compliance checks.</li>
              <li><strong>History:</strong> Review all your past inspections.</li>
            </ul>
          )}
          {role === 'admin' && (
            <ul className="list-disc pl-5 text-sm text-gray-600 space-y-2">
              <li><strong>Analytics:</strong> View platform-wide compliance data.</li>
              <li><strong>Rules:</strong> Manage the Legal Metrology compliance rules.</li>
            </ul>
          )}
        </div>
        <button 
          onClick={handleDismiss}
          className="w-full bg-indigo-600 text-white py-2 rounded-md font-medium hover:bg-indigo-700"
        >
          Got it, let's start!
        </button>
      </div>
    </div>
  );
};

export default OnboardingWalkthrough;
