import os
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

# Read environment variables
# required for all twilio access tokens
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CHAT_SERVICE_SID = os.getenv("TWILIO_CHAT_SERVICE_SID")
TWILIO_CHAT_API_KEY = os.getenv("TWILIO_CHAT_API_KEY")
TWILIO_CHAT_API_SECRET = os.getenv("TWILIO_CHAT_API_SECRET")
TWILIO_CHAT_ROLE_SID = os.getenv("TWILIO_CHAT_ROLE_SID")
TWILIO_CHAT_ROLE_SID_USER = os.getenv("TWILIO_CHAT_ROLE_SID_USER")

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

    # Create grants and add to token
    svc_grant = ChatGrant(
        service_sid=TWILIO_CHAT_SERVICE_SID, deployment_role_sid=TWILIO_CHAT_ROLE_SID
    )
    token.add_grant(svc_grant)

    user_grant = ChatGrant(
        service_sid=TWILIO_CHAT_SERVICE_SID,
        deployment_role_sid=TWILIO_CHAT_ROLE_SID_USER,
    )
    token.add_grant(user_grant)

    # Return token info as JSON
    # print(token.to_jwt())
    return token.to_jwt()
