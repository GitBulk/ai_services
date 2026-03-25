# Rails Integration Guide for Scam Detection API

## Integration Steps

### 1. Add HTTP Client Gem
```ruby
# Gemfile
gem 'httparty'
```

```bash
bundle install
```

### 2. Create ScamDetector Service
```ruby
# app/services/scam_detector.rb
class ScamDetector
  include HTTParty

  NOVA_AI_URL = ENV['NOVA_AI_URL'] || 'http://localhost:8000'
  SCAM_DETECTION_THRESHOLD = ENV['SCAM_DETECTION_THRESHOLD']&.to_i || 50

  def self.check_message(message, language = 'en')
    new.check_message(message, language)
  end

  def check_message(message, language = 'en')
    return { is_scam: false, reason: 'Empty message' } if message.blank?

    response = self.class.post(
      "#{NOVA_AI_URL}/api/v1/detect-scam",
      body: {
        message: message,
        language: language
      }.to_json,
      headers: { 'Content-Type' => 'application/json' },
      timeout: 10
    )
    
    parse_response(response)
  rescue StandardError => e
    Rails.logger.error("ScamDetector error: #{e.message}")
    { is_scam: false, error: true, reason: 'Service unavailable' }
  end
  
  private
  
  def parse_response(response)
    return { is_scam: false, error: true } unless response.success?
    
    data = response.parsed_response
    {
      is_scam: data['is_scam'],
      scam_score: data['scam_score'],
      reason: data['reason'],
      keywords_found: data['keywords_found'],
      context: data['context'],
      language: data['language']
    }
  end
end
```

### 3. Create Message Model Concern
```ruby
# app/models/concerns/scam_detectable.rb
module ScamDetectable
  extend ActiveSupport::Concern
  
  included do
    enum scam_status: { clean: 0, flagged: 1, blocked: 2, reviewed: 3 }
    
    before_save :detect_scam, if: :content_changed?
    
    validates :scam_score, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 100 }, allow_nil: true
  end
  
  def detect_scam
    result = ScamDetector.check_message(content, detect_language)
    
    self.scam_score = result[:scam_score]
    self.scam_reason = result[:reason]
    self.scam_keywords = result[:keywords_found].keys.join(',') if result[:keywords_found]
    
    # Set status based on score
    self.scam_status = case scam_score
                       when 0..40 then :clean
                       when 40..60 then :flagged
                       when 60..79 then :flagged
                       when 80..100 then :blocked
                       end
    
    # Notify moderators if flagged
    notify_moderators if scam_status == :blocked
  end
  
  def detect_language
    # Implement language detection for your app
    # Can use 'langdetect' gem or similar
    'en'  # Default to English
  end
  
  def notify_moderators
    ModeratorMailer.scam_message_detected(self).deliver_later
  end
  
  def censor_content
    update(content: "[Message censored due to scam detection]", scam_status: :blocked)
  end
end
```

### 4. Update Message Model
```ruby
# app/models/message.rb
class Message < ApplicationRecord
  belongs_to :sender, class_name: 'User'
  belongs_to :conversation
  
  include ScamDetectable
  
  # Add columns to track scam detection
  # - scam_score (decimal)
  # - scam_reason (text)
  # - scam_status (integer)
  # - scam_keywords (text)
end
```

### 5. Create Database Migration
```ruby
# db/migrate/XXXX_add_scam_detection_to_messages.rb
class AddScamDetectionToMessages < ActiveRecord::Migration[6.0]
  def change
    add_column :messages, :scam_score, :decimal, precision: 5, scale: 2, default: 0
    add_column :messages, :scam_reason, :text
    add_column :messages, :scam_status, :integer, default: 0
    add_column :messages, :scam_keywords, :string
    
    add_index :messages, :scam_status
    add_index :messages, :scam_score
  end
end
```

### 6. Update Message Serializer
```ruby
# app/serializers/message_serializer.rb
class MessageSerializer < ActiveModel::Serializer
  attributes :id, :content, :created_at, :sender_id
  
  # Only include scam info for admins or message owner
  attributes :scam_score, :scam_status, :scam_reason, :scam_keywords,
             if: :include_scam_info?
  
  def include_scam_info?
    current_user&.admin? || current_user&.id == object.sender_id
  end
end
```

### 7. Add Moderator Notifications
```ruby
# app/mailers/moderator_mailer.rb
class ModeratorMailer < ApplicationMailer
  def scam_message_detected(message)
    @message = message
    @sender = message.sender
    @conversation = message.conversation
    @scam_reason = message.scam_reason
    
    mail(to: Moderator.admin_emails, subject: "Scam Message Detected (Score: #{message.scam_score})")
  end
end
```

### 8. Add Rails Admin Interface
```ruby
# config/initializers/rails_admin.rb

RailsAdmin.config do |config|
  config.model 'Message' do
    list do
      field :id
      field :sender_id
      field :content
      field :scam_score
      field :scam_status
      field :scam_keywords
      field :scam_reason
      field :created_at
    end
    
    show do
      field :sender
      field :conversation
      field :content
      field :scam_reason
      field :scam_score
      field :scam_status
      field :scam_keywords
      field :created_at
    end
  end
end
```

### 9. Create Admin Dashboard View
```erb
<!-- app/views/admin/dashboard/_scam_stats.html.erb -->
<div class="stats-panel">
  <h3>Scam Detection Stats</h3>
  
  <ul>
    <li>
      Clean Messages (24h): 
      <strong><%= Message.where(scam_status: :clean, created_at: 24.hours.ago..).count %></strong>
    </li>
    <li>
      Flagged Messages: 
      <strong><%= Message.where(scam_status: :flagged, created_at: 24.hours.ago..).count %></strong>
    </li>
    <li>
      Blocked Messages: 
      <strong><%= Message.where(scam_status: :blocked, created_at: 24.hours.ago..).count %></strong>
    </li>
  </ul>
  
  <%= link_to 'Review Flagged Messages', admin_messages_path(scam_status: 'flagged') %>
</div>
```

### 10. Configure Environment Variables
```bash
# .env
NOVA_AI_URL=http://localhost:8000
SCAM_DETECTION_THRESHOLD=50
SCAM_DETECTION_ACTION_THRESHOLD=70
SCAM_MODERATOR_EMAIL=moderators@dating-app.com
```

## Workflow

### Message Flow
```
User sends message
    ↓
Message.create triggered
    ↓
ScamDetectable concern calls detect_scam
    ↓
ScamDetector calls Nova AI API
    ↓
Update message with scam_score, scam_status
    ↓
If score >= 80: Block message + Notify moderators
If score >= 50, < 80: Flag for review
If score < 50: Allow delivery as normal

Message sent to recipient (if not blocked)
```

### Moderation Flow
```
Admin Dashboard shows flagged/blocked messages
    ↓
Admin reviews message and context
    ↓
Admin decision:
  - Allow (set scam_status: reviewed)
  - Block (set scam_status: blocked)
  - Suspend sender (increment user.scam_violations)
  
If user.scam_violations >= 3: Auto-suspend account
```

## Testing

```ruby
# spec/services/scam_detector_spec.rb
RSpec.describe ScamDetector do
  describe '.check_message' do
    it 'detects telegram scam messages' do
      result = ScamDetector.check_message('Call me on telegram')
      expect(result[:is_scam]).to be true
      expect(result[:scam_score]).to be > 50
    end
    
    it 'handles legitimate messages' do
      result = ScamDetector.check_message('How are you today?')
      expect(result[:is_scam]).to be false
      expect(result[:scam_score]).to be < 50
    end
    
    it 'handles context-aware detection' do
      result = ScamDetector.check_message("I don't use telegram")
      expect(result[:is_scam]).to be false
    end
  end
end

# spec/models/message_spec.rb
RSpec.describe Message do
  describe 'scam detection' do
    it 'detects scam on save' do
      message = Message.new(content: 'Contact me on te.legram')
      message.save
      
      expect(message.scam_score).to be > 0
      expect(message.scam_status).to eq('flagged')
    end
  end
end
```

## Monitoring & Analytics

```ruby
# app/models/scam_stat.rb
class ScamStat < ApplicationRecord
  def self.record_detection(message)
    create!(
      message_id: message.id,
      scam_score: message.scam_score,
      scam_status: message.scam_status,
      keywords: message.scam_keywords,
      user_id: message.sender_id
    )
  end
  
  def self.get_daily_stats(date = Date.today)
    where(created_at: date.beginning_of_day..date.end_of_day).group_by(&:scam_status).map do |status, records|
      { status: status, count: records.count, average_score: records.average(:scam_score) }
    end
  end
end
```

## Performance Tuning

1. **Cache API responses** for same messages
```ruby
def check_message(message, language = 'en')
  Rails.cache.fetch("scam_detection:#{message.downcase.hash}", expires_in: 24.hours) do
    # API call
  end
end
```

2. **Batch process** messages in background
```ruby
# app/jobs/scam_detection_job.rb
class ScamDetectionJob < ApplicationJob
  def perform(message_id)
    message = Message.find(message_id)
    message.detect_scam
    message.save!
  end
end
```

3. **Use Redis** for rate limiting
```ruby
def check_message(message, language = 'en')
  if rate_limit_exceeded?
    return { is_scam: false, rate_limited: true }
  end
  
  # Continue as normal
end
```

## Troubleshooting

### Nova AI Service Down
- Messages should still be delivered but with `error: true`
- Manual review queued for moderation team
- Alert sent to devops

### False Positives
- Adjust `SCAM_DETECTION_THRESHOLD`
- Review blocked messages
- Retrain with feedback data

### False Negatives
- Monitor user reports of scammers
- Adjust thresholds per user behavior patterns
- Add new contact methods if missed
