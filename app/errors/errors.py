from app.errors import bp


@bp.errorhandler(404)
def page_not_found(e):
    return '', 404
