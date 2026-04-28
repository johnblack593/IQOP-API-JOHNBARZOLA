"""Module for IQ Option http login resource."""

from iqoptionapi.http.resource import Resource


class Login(Resource):
    """Class for IQ option login resource."""
    # pylint: disable=too-few-public-methods

    url = ""

    def _post(self, data=None, headers=None):
        """Send get request for IQ Option API login http resource.

        :returns: The instance of :class:`requests.Response`.
        """
        if headers is None:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Origin": "https://iqoption.com",
                "Referer": "https://iqoption.com/en/login",
                "Accept": "application/json",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            }
        return self.api.send_http_request_v2(method="POST", url="https://auth.iqoption.com/api/v2/login",data=data, headers=headers)

    def __call__(self, username, password):
        """Method to get IQ Option API login http request.

        :param str username: The username of a IQ Option server.
        :param str password: The password of a IQ Option server.

        :returns: The instance of :class:`requests.Response`.
        """
        data = {"identifier": username,
                "password": password}

        return self._post(data=data)
