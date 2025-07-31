import React from 'react';

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg';
    color?: string;
    className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
    size = 'md',
    color = '#3b82f6',
    className = ''
}) => {
    const sizeMap = {
        sm: '16px',
        md: '24px',
        lg: '32px'
    };

    return (
        <div className={`loading-spinner ${className}`}>
            <div
                className="spinner"
                style={{
                    width: sizeMap[size],
                    height: sizeMap[size],
                    borderColor: `${color}33`,
                    borderTopColor: color
                }}
            />
        </div>
    );
};
