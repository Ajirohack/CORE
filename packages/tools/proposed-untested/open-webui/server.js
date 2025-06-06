// server.js
const express = require('express');
const pool = require('./db');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Middleware for JWT authentication
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (token == null) return res.sendStatus(401);

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.sendStatus(403);
    req.user = user;
    next();
  });
}

// Initiate Invitation Code Issuance (Admin-Generated)
app.post('/admin/generate-invitation', authenticateToken, async (req, res) => {
  const { fullName, email, pin } = req.body;

  try {
    const invitationCode = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    await pool.query(
      'INSERT INTO invitations (code, full_name, pin) VALUES ($1, $2, $3) RETURNING *',
      [invitationCode, fullName, pin]
    );
    res.json({ invitationCode });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// QR Codes and PIN Authentication
app.post('/auth/verify-qr', async (req, res) => {
  const { qrCode, pin } = req.body;

  try {
    const result = await pool.query(
      'SELECT * FROM invitations WHERE code = $1 AND pin = $2',
      [qrCode, pin]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: 'Invalid QR Code or PIN' });
    }

    const user = result.rows[0];
    const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, { expiresIn: '1h' });
    res.json({ token });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// AI-Assisted Onboarding (Voice-Driven)
app.post('/auth/onboard', authenticateToken, async (req, res) => {
  const { fullName, policyConsent, voiceRecording } = req.body;

  try {
    // Verify that the user exists and is the one being onboarded
    const user = await pool.query(
      'SELECT * FROM invitations WHERE id = $1',
      [req.user.id]
    );

    if (user.rows.length === 0) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Verify that full name matches the invitation
    if (user.rows[0].full_name.toLowerCase() !== fullName.toLowerCase()) {
      return res.status(400).json({ message: 'Full name does not match invitation' });
    }

    // Check policy consent
    if (!policyConsent) {
      return res.status(400).json({ message: 'Policy consent is required' });
    }

    // Store voice recording for verification (optional)
    let recordingUrl = null;
    if (voiceRecording) {
      // Here you would normally upload the voice recording to a storage service
      // and save the URL. For this example, we'll just simulate that.
      recordingUrl = `recordings/${req.user.id}-${Date.now()}.wav`;
    }

    // Update user onboarding status
    await pool.query(
      'UPDATE invitations SET onboarding_complete = true, policy_consent = $1, voice_recording = $2, onboarding_date = NOW() WHERE id = $3',
      [policyConsent, recordingUrl, req.user.id]
    );

    // Create a new entry in pending_approvals table for admin review
    await pool.query(
      'INSERT INTO pending_approvals (invitation_id, status, created_at) VALUES ($1, $2, NOW()) RETURNING id',
      [req.user.id, 'pending']
    );

    res.json({ 
      message: 'Onboarding completed successfully. Your membership is pending admin approval.',
      status: 'pending_approval'
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Admin approval of memberships
app.post('/admin/approve-membership', authenticateToken, async (req, res) => {
  const { approvalId, approved } = req.body;

  try {
    // Verify admin permission
    if (!req.user.isAdmin) {
      return res.status(403).json({ message: 'Forbidden: Admin access required' });
    }

    // Get the pending approval
    const approval = await pool.query(
      'SELECT * FROM pending_approvals WHERE id = $1',
      [approvalId]
    );

    if (approval.rows.length === 0) {
      return res.status(404).json({ message: 'Approval request not found' });
    }

    // Update approval status
    await pool.query(
      'UPDATE pending_approvals SET status = $1, approved_by = $2, approved_at = NOW() WHERE id = $3',
      [approved ? 'approved' : 'rejected', req.user.id, approvalId]
    );

    if (approved) {
      // Create a permanent membership record
      const invitation = await pool.query(
        'SELECT * FROM invitations WHERE id = $1',
        [approval.rows[0].invitation_id]
      );

      if (invitation.rows.length > 0) {
        // Generate a secure membership key
        const membershipKey = crypto.randomBytes(32).toString('hex');
        
        // Create the membership record
        await pool.query(
          'INSERT INTO memberships (user_id, membership_key, email, full_name, created_at, status) VALUES ($1, $2, $3, $4, NOW(), $5)',
          [invitation.rows[0].id, membershipKey, invitation.rows[0].email, invitation.rows[0].full_name, 'active']
        );
      }
    }

    res.json({ 
      message: approved ? 'Membership approved successfully' : 'Membership rejected',
      status: approved ? 'approved' : 'rejected' 
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Get membership status
app.get('/auth/membership-status', authenticateToken, async (req, res) => {
  try {
    // Check if user has an active membership
    const membership = await pool.query(
      'SELECT * FROM memberships WHERE user_id = $1',
      [req.user.id]
    );

    if (membership.rows.length === 0) {
      // Check if user has a pending approval
      const pendingApproval = await pool.query(
        'SELECT * FROM pending_approvals WHERE invitation_id = $1 AND status = $2',
        [req.user.id, 'pending']
      );

      if (pendingApproval.rows.length > 0) {
        return res.json({ status: 'pending_approval' });
      }

      return res.json({ status: 'not_member' });
    }

    res.json({ 
      status: membership.rows[0].status,
      membershipKey: membership.rows[0].membership_key,
      memberSince: membership.rows[0].created_at
    });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
