// client.js
const axios = require('axios');

async function generateInvitation() {
  const adminToken = 'your_admin_jwt_token'; // Replace with a valid admin token
  const response = await axios.post(
    'http://localhost:3000/admin/generate-invitation',
    {
      fullName: 'John Doe',
      email: 'john.doe@example.com',
      pin: '1234',
    },
    {
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
    }
  );
  console.log(response.data);
}

async function verifyQR() {
  const response = await axios.post('http://localhost:3000/auth/verify-qr', {
    qrCode: 'your_invitation_code',
    pin: '1234',
  });
  console.log(response.data);
}

async function onboard() {
  const token = eyJkZXRhaWwiOiJNZXRob2QgTm90IEFsbG93ZWQifQ; // Replace with a valid token
  const response = await axios.post(
    'http://localhost:3000/auth/onboard',
    {
      fullName: 'John Doe',
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  console.log(response.data);
}

// Uncomment the function you want to test
// generateInvitation();
// verifyQR();
// onboard();
