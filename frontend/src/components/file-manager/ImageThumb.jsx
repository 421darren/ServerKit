import useImagePreview from './hooks/useImagePreview';

export default function ImageThumb({ path, fileApi, fallback, className = 'thumb-image', alt = '' }) {
    const src = useImagePreview(fileApi, path);
    if (!src) return fallback;
    return <img src={src} alt={alt} className={className} loading="lazy" />;
}
