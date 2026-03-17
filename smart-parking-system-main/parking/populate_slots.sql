-- in pgAdmin, run this to populate the parking slots:
-- إدراج A1-A50
INSERT INTO public.parking_parkingslot (slot_number, status, slot_type, row, col, floor)
SELECT 'A' || n AS slot_number, 'available', 'regular', 1, n, 1
FROM generate_series(1,50) AS n;

-- إدراج B1-B17
INSERT INTO public.parking_parkingslot (slot_number, status, slot_type, row, col, floor)
SELECT 'B' || n AS slot_number, 'available', 'regular', 2, n, 1
FROM generate_series(1,17) AS n;

-- إدراج C1-C17
INSERT INTO public.parking_parkingslot (slot_number, status, slot_type, row, col, floor)
SELECT 'C' || n AS slot_number, 'available', 'regular', 3, n, 1
FROM generate_series(1,17) AS n;

-- إدراج D1-D45
INSERT INTO public.parking_parkingslot (slot_number, status, slot_type, row, col, floor)
SELECT 'D' || n AS slot_number, 'available', 'regular', 4, n, 1
FROM generate_series(1,45) AS n;

-- تأكيد البيانات
SELECT * FROM public.parking_parkingslot
ORDER BY id ASC;
