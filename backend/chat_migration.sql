-- Add pinning columns to team_messages (safe to run if already exist)
ALTER TABLE team_messages ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE team_messages ADD COLUMN IF NOT EXISTS pinned_by UUID REFERENCES employees(id) ON DELETE SET NULL;

-- Create direct_messages table
CREATE TABLE IF NOT EXISTS direct_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast DM lookup between two users
CREATE INDEX IF NOT EXISTS idx_dm_sender_receiver ON direct_messages(sender_id, receiver_id);
CREATE INDEX IF NOT EXISTS idx_dm_receiver_unread ON direct_messages(receiver_id, is_read);
