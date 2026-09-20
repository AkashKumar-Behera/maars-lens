import { Upload, Camera, Trash2 } from 'lucide-react';
import { useRef, useState, useEffect } from 'react';

const ImageUpload = ({ onUpload, currentFile = null, error = null }) => {
  const fileInputRef = useRef(null);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    if (!currentFile) {
      setPreview(null);
    }
  }, [currentFile]);

  const processFile = (file) => {
    if (!file) {
      setPreview(null);
      onUpload?.(null);
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result);
    };
    reader.readAsDataURL(file);
    onUpload?.(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      processFile(file);
    }
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onUpload?.(null);
  };

  return (
    <div className="w-full">
      {!preview ? (
        <div
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
            error
              ? 'border-rose-500/80 bg-rose-950/20 hover:bg-rose-950/30'
              : 'border-slate-700 bg-slate-900/60 hover:bg-slate-800/60 hover:border-indigo-500/80'
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <div className="flex justify-center space-x-3 mb-3 text-indigo-400">
            <Camera size={30} />
            <Upload size={30} />
          </div>
          <p className="text-sm font-semibold text-slate-200">
            Click to take a photo or select an image
          </p>
          <p className="text-xs text-slate-400 mt-1.5">
            Supports JPEG, PNG, and WebP (Max 15MB)
          </p>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileChange}
          />
        </div>
      ) : (
        <div className="relative rounded-xl overflow-hidden border border-slate-700 bg-slate-950 shadow-lg">
          <img
            src={preview}
            alt="Uploaded label preview"
            className="w-full h-auto max-h-[50vh] object-contain mx-auto"
          />
          <div className="p-3 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between">
            <span className="text-xs text-slate-300 truncate font-mono">
              {currentFile?.name || 'Selected image preview'}
            </span>
            <button
              type="button"
              onClick={handleRemove}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-semibold rounded-lg transition"
            >
              <Trash2 size={14} />
              <span>Remove / Reselect</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageUpload;
