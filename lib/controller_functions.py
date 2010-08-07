from gaesessions import get_current_session

def is_logged_in(h=None):
    """Checks if the user is logged in.  If not, False is returned and (if
    h is not None) then h.redirect is called.  Otherwise the session is returned.
    """
    session = get_current_session()
    if not session.is_active() or not session.has_key('my_id'):
        if h:
            redir_url = '/login?redir_to=' + h.request.path
            if h.request.query_string:
                redir_url += '?' + h.request.query_string.replace('&', '@$@')
            h.redirect(redir_url)
        return False
    return session

def login_required(h):
    return is_logged_in(h)
