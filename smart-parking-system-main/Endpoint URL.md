#### Enter API
http://127.0.0.1:8000/api/entry/
POST Request
multipart/form-data
```
	`license_plate` -> String
	`entry_image` ->File (Image)
    `car_embedding` ->List[Float]
    `car_color` ->String
    `camera_id` ->Integer

```

	
Response
```
{
    "status": "success",
    "log_id": 45,
    "identified_user": "Omar Ahmed" | "Guest",
    "target_slot": "A1",
    "entry_time": "2026-03-19T14:30:00Z",
    "message": "تم تسجيل الدخول وتخصيص مكان بنجاح"
}
```
___
#### Exit API
http://127.0.0.1:8000/api/exit/
POST Request
multipart/form-data
```
	`license_plate`: (String)
	`exit_image`: (File)
```

Response
```
{
    "status": "success",
    "message": "Vehicle exit recorded successfully",
    "summary": {
        "plate": "ABC 123",
        "entry_time": "2026-03-19T10:00:00Z",
        "exit_time": "2026-03-19T14:30:00Z",
        "duration_hours": 5, 
        "total_fee": 125.00
    }
}
```

___
http://127.0.0.1:8000/api/track
POST Request
{
    "car_embedding": [0.12, -0.5, 0.88, "..."],
    "camera_id": "CAM_ZONE_05",
    "car_color": "black"
}

Success Response (200 OK):
{
    "status": "success",
    "identified_plate": "ABC 123",
    "confidence_score": 0.145,
    "current_zone": "Zone B - Ground Floor",
    "message": "Vehicle ABC 123 tracked at Zone B"
}
___

#### Slots Update API (Bulk)

[http://127.0.0.1:8000/api/slots/update/](https://www.google.com/search?q=http://127.0.0.1:8000/api/slots/update/) 
POST Request 
**application/json**
```
[
    {
        "slot_id": "A1",
        "is_occupied": true
    },
    {
        "slot_id": "A2",
        "is_occupied": false
    }
]
```

**Response**
```
{
    "status": "success",
    "updated_slots": ["A1", "A2"],
    "message": "Successfully updated 2 slots"
}
```

---


#### Parking Summary API

[http://127.0.0.1:8000/api/status/summary/]
GET Request
**Response**

```
{
    "total_slots": 100,
    "available": 65,
    "occupied": 25,
    "reserved": 10
}
```