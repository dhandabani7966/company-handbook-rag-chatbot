import React, { useState } from 'react';
import { Star, Send, ArrowLeft, CheckCircle, MessageSquare } from 'lucide-react';

export default function FeedbackPage({ apiBase, token, onBackToChat }) {
  const [rating, setRating] = useState(5);
  const [hoverRating, setHoverRating] = useState(0);
  const [category, setCategory] = useState('Accuracy & Citations');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;

    try {
      setSubmitting(true);
      setError('');
      const res = await fetch(`${apiBase}/api/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          rating,
          category,
          comment: comment.trim()
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Feedback submission failed');
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const categories = [
    'Accuracy & Citations',
    'UI & Experience',
    'Speed & Performance',
    'Missing Handbook Section',
    'General Suggestions'
  ];

  return (
    <div className="enterprise-page-container">
      {/* Header */}
      <div className="page-header-row">
        <div>
          <button className="back-breadcrumb-btn" onClick={onBackToChat}>
            <ArrowLeft size={16} />
            <span>Back to Chat</span>
          </button>
          <h2>Share Your Feedback</h2>
          <p className="page-subtitle">
            Help us refine answer relevance, citation accuracy, and workplace assistance.
          </p>
        </div>
      </div>

      <div className="feedback-form-wrapper">
        {submitted ? (
          <div className="feedback-success-card">
            <CheckCircle size={48} color="#16A34A" />
            <h3>Thank You for Your Feedback!</h3>
            <p>
              Your thoughts and ratings directly inform our retrieval ranking and accuracy benchmarks.
            </p>
            <div className="feedback-success-actions">
              <button
                className="primary-action-btn"
                onClick={() => {
                  setSubmitted(false);
                  setComment('');
                  setRating(5);
                }}
              >
                Submit Another Response
              </button>
              <button className="secondary-action-btn" onClick={onBackToChat}>
                Return to Chat
              </button>
            </div>
          </div>
        ) : (
          <div className="feedback-card">
            <form onSubmit={handleSubmit} className="feedback-actual-form">
              {error && <div className="login-error-alert">{error}</div>}

              {/* Star Rating Selection */}
              <div className="feedback-rating-group">
                <label className="feedback-label">How satisfied are you with Handbook AI's answers?</label>
                <div className="stars-row">
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isFilled = (hoverRating || rating) >= star;
                    return (
                      <button
                        key={star}
                        type="button"
                        className="star-btn"
                        onMouseEnter={() => setHoverRating(star)}
                        onMouseLeave={() => setHoverRating(0)}
                        onClick={() => setRating(star)}
                      >
                        <Star
                          size={32}
                          fill={isFilled ? '#F97316' : 'none'}
                          color={isFilled ? '#F97316' : '#D1D5DB'}
                        />
                      </button>
                    );
                  })}
                  <span className="rating-score-text">
                    {rating} out of 5 stars ({rating === 5 ? 'Excellent' : rating >= 4 ? 'Good' : rating >= 3 ? 'Average' : 'Needs Improvement'})
                  </span>
                </div>
              </div>

              {/* Category Dropdown */}
              <div className="form-group">
                <label className="feedback-label">Feedback Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="feedback-select"
                >
                  {categories.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>

              {/* Comment Textarea */}
              <div className="form-group">
                <label className="feedback-label">Your Comments & Observations</label>
                <textarea
                  required
                  rows={5}
                  placeholder="Tell us what worked well or what policy answers could be improved..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="feedback-textarea"
                />
              </div>

              <div className="feedback-actions">
                <button
                  type="submit"
                  className="primary-action-btn large"
                  disabled={submitting || !comment.trim()}
                >
                  <Send size={18} />
                  <span>{submitting ? 'Submitting...' : 'Submit Feedback'}</span>
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
