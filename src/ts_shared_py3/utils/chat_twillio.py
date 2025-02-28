import os
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

# required for all twilio access tokens
# account_sid = "ACd6e851e0f16d71160c8dccb0278ae09c"
# api_key = "SKd182c4c12db7894e1b6f81ad1be65717"
# api_secret = "SwFkxpRsEXRPGRq4aNhDwSIaVacQa2lA"

# # required for Chat grants
# service_sid = "IS2c7aa5f3ee9745aba81d31075187d6b2"
# # identity = 'user@example.com'

# Read environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CHAT_SERVICE_SID = os.getenv("TWILIO_CHAT_SERVICE_SID")
TWILIO_CHAT_API_KEY = os.getenv("TWILIO_CHAT_API_KEY")
TWILIO_CHAT_API_SECRET = os.getenv("TWILIO_CHAT_API_SECRET")
# TWILIO_CHAT_ROLE_SID = os.getenv("TWILIO_CHAT_ROLE_SID")

# Debug Output (Ensure sensitive values are not logged in production)
# print(f"✅ TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID}")
# print(f"✅ TWILIO_AUTH_TOKEN: {'SET' if TWILIO_AUTH_TOKEN else 'MISSING'}")
# print(f"✅ TWILIO_CHAT_SERVICE_SID: {TWILIO_CHAT_SERVICE_SID}")
# print(f"✅ TWILIO_CHAT_ROLE_SID: {TWILIO_CHAT_ROLE_SID}")
# print(f"✅ TWILIO_CHAT_API_KEY: {TWILIO_CHAT_API_KEY}")
# print(f"✅ TWILIO_CHAT_API_SECRET: {'SET' if TWILIO_CHAT_API_SECRET else 'MISSING'}")


def getTwillioChatAccessToken(userId: str) -> str:
    """"""
    assert isinstance(userId, str), "invalid arg"
    # Create access token with credentials
    token = AccessToken(
        TWILIO_ACCOUNT_SID,
        TWILIO_CHAT_API_KEY,
        TWILIO_CHAT_API_SECRET,
        identity=userId,
        ttl=23 * 3600,
    )

    # Create an Chat grant and add to token
    chat_grant = ChatGrant(service_sid=TWILIO_CHAT_SERVICE_SID)
    token.add_grant(chat_grant)

    # Return token info as JSON
    # print(token.to_jwt())
    return token.to_jwt()
