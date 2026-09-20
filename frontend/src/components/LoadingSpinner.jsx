const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
  const sizeClass = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-12 h-12' : 'w-8 h-8';
  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`animate-spin rounded-full border-b-2 border-indigo-600 ${sizeClass}`}></div>
      {text && <span className="mt-2 text-sm text-gray-500">{text}</span>}
    </div>
  );
};

export default LoadingSpinner;
