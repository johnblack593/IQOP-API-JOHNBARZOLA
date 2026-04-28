"""Module for IQ option websocket."""

def underlying_list(api, message):
    if message["name"] != "underlying-list":
        return
    
    api.underlying_list_data = message["msg"]
    
    items = message.get("msg", {}).get("items", [])
    if not items:
        ev = getattr(api, "underlying_list_data_event", None)
        if ev: ev.set()
        return
    
    # Identificar categoría desde el primer item
    category = None
    if items:
        first = items[0]
        category = (
            first.get("instrument_type") or
            first.get("type") or
            first.get("active_type") or
            "unknown"
        )
    
    # Acumular en store separado por categoría
    if not hasattr(api, "_instruments_by_category"):
        api._instruments_by_category = {}
    
    api._instruments_by_category[category] = items
    
    # También mantener compatibilidad con api.instruments como lista completa
    all_items = []
    for cat_items in api._instruments_by_category.values():
        all_items.extend(cat_items)
    api.instruments = {"instruments": all_items}
    
    # Disparar evento para desbloquear stable_api
    if hasattr(api, 'instruments_event'):
        api.instruments_event.set()
    
    ev = getattr(api, "underlying_list_data_event", None)
    if ev: ev.set()
