from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

# required for all twilio access tokens
account_sid = "ACd6e851e0f16d71160c8dccb0278ae09c"
api_key = "SKd182c4c12db7894e1b6f81ad1be65717"
api_secret = "SwFkxpRsEXRPGRq4aNhDwSIaVacQa2lA"

# required for Chat grants
service_sid = "IS2c7aa5f3ee9745aba81d31075187d6b2"
# identity = 'user@example.com'


def getTwillioChatAccessToken(identity):
    """"""
    assert isinstance(identity, str), "invalid arg"
    # Create access token with credentials
    token = AccessToken(
        account_sid, api_key, api_secret, identity=identity, ttl=23 * 3600
    )

    # Create an Chat grant and add to token
    chat_grant = ChatGrant(service_sid=service_sid)
    token.add_grant(chat_grant)

    # Return token info as JSON
    print(token.to_jwt())
    return token.to_jwt()
