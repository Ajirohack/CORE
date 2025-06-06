// seed.js
const pool = require('./db');

async function seed() {
  try {
    const users = [
      { full_name: 'John Doe', email: 'john.doe@example.com', pin: '1234' },
      { full_name: 'Jane Smith', email: 'jane.smith@example.com', pin: '5678' },
    ];

    for (const user of users) {
      const invitationCode = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
      await pool.query(
        'INSERT INTO invitations (code, full_name, pin) VALUES ($1, $2, $3)',
        [invitationCode, user.full_name, user.pin]
      );
      console.log(`Invitation Code for ${user.full_name}: ${invitationCode}`);
    }
  } catch (err) {
    console.error(err.message);
  } finally {
    pool.end();
  }
}

seed();
