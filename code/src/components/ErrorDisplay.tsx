import React from 'react';

interface ErrorBoundaryProps {
    error: string | null;
    onRetry?: () => void;
    className?: string;
}

export const ErrorDisplay: React.FC<ErrorBoundaryProps> = ({
    error,
    onRetry,
    className = ''
}) => {
    if (!error) return null;

    return (
        <div className={`error-display ${className}`}>
            <div className="error-content">
                <div className="error-icon">⚠️</div>
                <div className="error-message">
                    <h3>Something went wrong</h3>
                    <p>{error}</p>
                </div>
                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="error-retry-button"
                    >
                        Try Again
                    </button>
                )}
            </div>
        </div>
    );
};
