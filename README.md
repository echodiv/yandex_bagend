Yandex Backend school test case

Openapi3 service
Flask, sqlalchemy


API:
/couriers 
HTTP methods: POST

POST:
 - HTTP codes: 201, 400

/couriers/{id} 
id is mondatory param
HTTP methods: GET | PATCH

GET:
 - HTTP codes: 200, 400
PATCH:
 - HTTP codes: 200, 400, 404


/orders
HTTP methods: POST
POST:
 - HTTP codes: 201, 400

/orders/assign
HTTP methods: POST
POST:
 - HTTP codes: 200, 400

/orders/complete
HTTP methods: POST
POST:
 - HTTP codes: 200, 400