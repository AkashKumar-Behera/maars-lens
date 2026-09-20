import { FolderSearch } from 'lucide-react';

const EmptyState = ({ title = 'No data found', message = 'There is nothing to display here right now.', icon: Icon = FolderSearch }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center bg-white border border-dashed border-gray-300 rounded-lg">
      <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
        <Icon size={32} className="text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900">{title}</h3>
      <p className="mt-1 text-sm text-gray-500 max-w-sm">{message}</p>
    </div>
  );
};

export default EmptyState;
