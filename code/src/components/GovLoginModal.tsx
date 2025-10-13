import React, { useState } from 'react';
import type { GovAuthCredentials, GovSignupData } from '../types';

interface GovLoginModalProps {
    isOpen: boolean;
    onClose: () => void;
    onLogin: (credentials: GovAuthCredentials) => Promise<void>;
    onSignup: (data: GovSignupData) => Promise<void>;
}

export const GovLoginModal: React.FC<GovLoginModalProps> = ({
    isOpen,
    onClose,
    onLogin,
    onSignup
}) => {
    const [isLoginMode, setIsLoginMode] = useState(true);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [loginForm, setLoginForm] = useState<GovAuthCredentials>({
        username: '',
        password: ''
    });

    const [signupForm, setSignupForm] = useState<GovSignupData>({
        username: '',
        email: '',
        password: '',
        full_name: '',
        department: ''
    });

    if (!isOpen) return null;

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await onLogin(loginForm);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            await onSignup(signupForm);
            setIsLoginMode(true); // Switch to login after successful signup
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Signup failed');
        } finally {
            setLoading(false);
        }
    };

    const resetForms = () => {
        setLoginForm({ username: '', password: '' });
        setSignupForm({ username: '', email: '', password: '', full_name: '', department: '' });
        setError(null);
    };

    const switchMode = () => {
        setIsLoginMode(!isLoginMode);
        resetForms();
    };

    return (
        <div className="modal-overlay">
            <div className="gov-auth-modal">
                <div className="modal-header">
                    <h2>🏛️ Government Authorization</h2>
                    <button className="close-button" onClick={onClose}>×</button>
                </div>

                <div className="modal-body">
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}

                    {isLoginMode ? (
                        <form onSubmit={handleLogin} className="auth-form">
                            <h3>Login</h3>

                            <div className="form-group">
                                <label htmlFor="username">Username:</label>
                                <input
                                    type="text"
                                    id="username"
                                    value={loginForm.username}
                                    onChange={(e) => setLoginForm(prev => ({ ...prev, username: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="password">Password:</label>
                                <input
                                    type="password"
                                    id="password"
                                    value={loginForm.password}
                                    onChange={(e) => setLoginForm(prev => ({ ...prev, password: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-actions">
                                <button
                                    type="submit"
                                    className="auth-submit-button"
                                    disabled={loading}
                                >
                                    {loading ? 'Logging in...' : 'Login'}
                                </button>
                                <button
                                    type="button"
                                    className="auth-back-button"
                                    onClick={onClose}
                                    disabled={loading}
                                >
                                    Back
                                </button>
                            </div>

                            <div className="auth-switch">
                                <p>Don't have an account?
                                    <button
                                        type="button"
                                        className="link-button"
                                        onClick={switchMode}
                                        disabled={loading}
                                    >
                                        Sign Up
                                    </button>
                                </p>
                            </div>
                        </form>
                    ) : (
                        <form onSubmit={handleSignup} className="auth-form">
                            <h3>Sign Up</h3>

                            <div className="form-group">
                                <label htmlFor="signup-username">Username:</label>
                                <input
                                    type="text"
                                    id="signup-username"
                                    value={signupForm.username}
                                    onChange={(e) => setSignupForm(prev => ({ ...prev, username: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="signup-email">Email:</label>
                                <input
                                    type="email"
                                    id="signup-email"
                                    value={signupForm.email}
                                    onChange={(e) => setSignupForm(prev => ({ ...prev, email: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="signup-fullname">Full Name:</label>
                                <input
                                    type="text"
                                    id="signup-fullname"
                                    value={signupForm.full_name}
                                    onChange={(e) => setSignupForm(prev => ({ ...prev, full_name: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="signup-department">Department (Optional):</label>
                                <input
                                    type="text"
                                    id="signup-department"
                                    value={signupForm.department}
                                    onChange={(e) => setSignupForm(prev => ({ ...prev, department: e.target.value }))}
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="signup-password">Password:</label>
                                <input
                                    type="password"
                                    id="signup-password"
                                    value={signupForm.password}
                                    onChange={(e) => setSignupForm(prev => ({ ...prev, password: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-actions">
                                <button
                                    type="submit"
                                    className="auth-submit-button"
                                    disabled={loading}
                                >
                                    {loading ? 'Signing up...' : 'Sign Up'}
                                </button>
                                <button
                                    type="button"
                                    className="auth-back-button"
                                    onClick={onClose}
                                    disabled={loading}
                                >
                                    Back
                                </button>
                            </div>

                            <div className="auth-switch">
                                <p>Already have an account?
                                    <button
                                        type="button"
                                        className="link-button"
                                        onClick={switchMode}
                                        disabled={loading}
                                    >
                                        Login
                                    </button>
                                </p>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
};
