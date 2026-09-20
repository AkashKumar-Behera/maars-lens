import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

const QualityFeedback = ({ issues = [], onRetake, onProceed }) => {
  if (issues.length === 0) return null;

  const getFeedbackMessage = (issue) => {
    switch (issue) {
      case 'blur': return { title: 'Image is too blurry', advice: 'Hold steady and ensure the text is in focus before capturing.' };
      case 'glare': return { title: 'Glare detected', advice: 'Change angle to avoid direct light reflecting off the package.' };
      case 'low_brightness': return { title: 'Image is too dark', advice: 'Move to a better-lit area or use a flash.' };
      case 'overexposure': return { title: 'Image is overexposed', advice: 'Avoid direct bright light or adjust exposure.' };
      case 'small_text': return { title: 'Text not clearly visible', advice: 'Move closer to the label so text occupies more of the frame.' };
      case 'low_resolution': return { title: 'Resolution too low', advice: 'Use a higher resolution camera setting.' };
      default: return { title: 'Image quality issue', advice: 'Please capture a clearer image.' };
    }
  };

  const isSevere = issues.length > 1 || issues.includes('blur') || issues.includes('small_text');

  return (
    <div className={`p-4 rounded-md border ${isSevere ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
      <div className="flex items-start mb-3">
        {isSevere ? <AlertTriangle className="text-red-500 mr-2 shrink-0 mt-0.5" /> : <Info className="text-yellow-600 mr-2 shrink-0 mt-0.5" />}
        <div>
          <h3 className={`font-semibold ${isSevere ? 'text-red-800' : 'text-yellow-800'}`}>
            Image quality issues detected
          </h3>
          <ul className="mt-2 space-y-2">
            {issues.map(issue => {
              const { title, advice } = getFeedbackMessage(issue);
              return (
                <li key={issue} className="text-sm">
                  <span className="font-medium text-gray-800">{title}: </span>
                  <span className="text-gray-600">{advice}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
      <div className="mt-4 flex space-x-3">
        <button 
          onClick={onRetake}
          className={`px-4 py-2 text-white text-sm font-medium rounded shadow-sm ${isSevere ? 'bg-red-600 hover:bg-red-700' : 'bg-yellow-600 hover:bg-yellow-700'}`}
        >
          Retake Photo
        </button>
        {!isSevere && onProceed && (
          <button 
            onClick={onProceed}
            className="px-4 py-2 bg-white text-gray-700 text-sm font-medium border border-gray-300 rounded shadow-sm hover:bg-gray-50"
          >
            Proceed Anyway
          </button>
        )}
      </div>
    </div>
  );
};

export default QualityFeedback;
