"""Module for IQ option websocket."""

def underlying_list(api, message):
    name = message.get("name")
    
    if name in ("underlying-list", "underlying-list-changed"):
        items = message.get("msg", {}).get("items", [])
        if not items and name == "underlying-list":
            ev = getattr(api, "underlying_list_data_event", None)
            if ev: ev.set()
            return
            
        # Identificar categoría desde el primer item
        category = "unknown"
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
        
        # En caso de 'changed', podríamos querer mergear en lugar de reemplazar, 
        # pero para simplificar y dado que el browser suele enviar la lista de la categoría completa:
        api._instruments_by_category[category] = items
        
        # Mantener compatibilidad con api.instruments
        all_items = []
        for cat_items in api._instruments_by_category.values():
            all_items.extend(cat_items)
        api.instruments = {"instruments": all_items}
        
        # Disparar eventos
        if hasattr(api, 'instruments_event'):
            api.instruments_event.set()
        
        ev = getattr(api, "underlying_list_data_event", None)
        if ev: ev.set()
