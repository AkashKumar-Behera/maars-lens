import { useState } from 'react';
import { X, HelpCircle } from 'lucide-react';

const Help = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 bg-indigo-600 text-white p-3 rounded-full shadow-lg hover:bg-indigo-700"
      >
        <HelpCircle size={24} />
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-end z-50">
          <div className="w-full max-w-sm bg-white h-full shadow-xl flex flex-col">
            <div className="p-4 border-b flex justify-between items-center bg-indigo-50">
              <h2 className="text-xl font-bold text-indigo-900">Help & Support</h2>
              <button onClick={() => setIsOpen(false)} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <h3 className="font-semibold text-lg mb-2">Frequently Asked Questions</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">How do I perform a scan?</h4>
                  <p className="text-sm text-gray-600">Navigate to the dashboard and click "Start New Scan". Follow the on-screen instructions to capture the product image.</p>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">What if an image is rejected?</h4>
                  <p className="text-sm text-gray-600">Ensure the lighting is good, text is legible, and there is no glare. You will see specific feedback on how to improve.</p>
                </div>
              </div>
              
              <div className="mt-8 border-t pt-4">
                <h3 className="font-semibold text-lg mb-2">Contact Support</h3>
                <p className="text-sm text-gray-600">Email: support@maarslens.gov</p>
                <p className="text-sm text-gray-600">Phone: 1800-111-2222</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Help;
