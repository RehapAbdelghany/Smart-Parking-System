--
-- PostgreSQL database dump
--

\restrict L8QKrMpWwt4Hhu31s61EeszMI24LKLzYhAyyasimYr6ReRnPrfQUMQWtpYKoRwE

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.1

-- Started on 2026-03-19 19:44:02

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 5055 (class 0 OID 16424)
-- Dependencies: 226
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- TOC entry 5051 (class 0 OID 16402)
-- Dependencies: 222
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	group
3	auth	permission
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	parking	parkingslot
8	parking	reservation
9	parking	vehiclelog
10	parking	camera
\.


--
-- TOC entry 5053 (class 0 OID 16414)
-- Dependencies: 224
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	3	add_permission
6	Can change permission	3	change_permission
7	Can delete permission	3	delete_permission
8	Can view permission	3	view_permission
9	Can add group	2	add_group
10	Can change group	2	change_group
11	Can delete group	2	delete_group
12	Can view group	2	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add parking slot	7	add_parkingslot
26	Can change parking slot	7	change_parkingslot
27	Can delete parking slot	7	delete_parkingslot
28	Can view parking slot	7	view_parkingslot
29	Can add reservation	8	add_reservation
30	Can change reservation	8	change_reservation
31	Can delete reservation	8	delete_reservation
32	Can view reservation	8	view_reservation
33	Can add vehicle log	9	add_vehiclelog
34	Can change vehicle log	9	change_vehiclelog
35	Can delete vehicle log	9	delete_vehiclelog
36	Can view vehicle log	9	view_vehiclelog
37	Can add camera	10	add_camera
38	Can change camera	10	change_camera
39	Can delete camera	10	delete_camera
40	Can view camera	10	view_camera
\.


--
-- TOC entry 5057 (class 0 OID 16434)
-- Dependencies: 228
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- TOC entry 5059 (class 0 OID 16443)
-- Dependencies: 230
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
2	pbkdf2_sha256$1200000$5Q0AUvwe50Zkwp19UwQDpD$+MzRPp37IHuWDHmWiuQHBBo0Nc/vw7I2Ms/nzhepzxg=	\N	f	Omar3yad	Omar	Ahmed	Omar3yad@gmail.com	f	t	2026-03-05 02:05:31.48287+02
3	pbkdf2_sha256$1200000$6FtTGLDc1gadBu5ygQwLhH$2JBKDlPxCVXGrg76Qep4cNvjIiXPJiCNiTCeDwAaWmM=	\N	f	Omarayad	Omar	Ayyad	Omarayad@gmail.com	f	t	2026-03-06 00:49:07.004417+02
4	pbkdf2_sha256$1200000$fwM8TegBXaoiE250tIW5hm$CATozIaaLa/4NU/TwbpQSDJK39nhgrWPndMABvEm3Ho=	\N	f	Omarahmed	Omar	Ahmed	Omarahmed@gmail.com	f	t	2026-03-06 00:53:33.011039+02
1	pbkdf2_sha256$1200000$3zKCh01WAEAI1D9wVVe7vI$TzDNcDIdA1doWr8uahwO2hgqqA1XmI9YjqM/5wHFTa0=	2026-03-15 16:06:34.707874+02	t	admin				t	t	2026-03-04 13:14:01.061195+02
\.


--
-- TOC entry 5061 (class 0 OID 16462)
-- Dependencies: 232
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- TOC entry 5063 (class 0 OID 16471)
-- Dependencies: 234
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- TOC entry 5065 (class 0 OID 16532)
-- Dependencies: 236
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
1	2026-03-04 13:16:30.305065+02	1	Slot 1 - available	1	[{"added": {}}]	7	1
2	2026-03-04 13:16:42.07643+02	2	Slot 2 - available	1	[{"added": {}}]	7	1
3	2026-03-04 13:16:45.650844+02	3	Slot 3 - available	1	[{"added": {}}]	7	1
4	2026-03-04 13:16:48.686962+02	4	Slot 4 - available	1	[{"added": {}}]	7	1
5	2026-03-04 13:17:24.845252+02	1	Res 55 for admin	1	[{"added": {}}]	8	1
6	2026-03-15 16:18:11.07737+02	7	Slot A5 - available	1	[{"added": {}}]	7	1
7	2026-03-15 16:46:38.08004+02	7	Slot A5 - available (Row 0, Col 0)	3		7	1
8	2026-03-15 16:46:38.080117+02	4	Slot 4 - available (Row 0, Col 0)	3		7	1
9	2026-03-15 16:46:38.080156+02	3	Slot 3 - occupied (Row 0, Col 0)	3		7	1
10	2026-03-15 16:46:38.080186+02	2	Slot 2 - available (Row 0, Col 0)	3		7	1
11	2026-03-15 16:46:38.080213+02	1	Slot 1 - occupied (Row 0, Col 0)	3		7	1
12	2026-03-19 03:50:03.912565+02	1	Res 55e for Omarahmed	1	[{"added": {}}]	8	1
13	2026-03-19 03:55:22.008102+02	1	Camera CAM-01 - Zone zone-A1	1	[{"added": {}}]	10	1
14	2026-03-19 04:11:02.579081+02	1	Res RES123 for Omarahmed	2	[{"changed": {"fields": ["Reservation code", "Start time", "End time"]}}]	8	1
15	2026-03-19 04:16:55.612747+02	1	Res RES123 for Omarahmed	2	[{"changed": {"fields": ["\\u0631\\u0642\\u0645 \\u0627\\u0644\\u0644\\u0648\\u062d\\u0629"]}}]	8	1
16	2026-03-19 13:40:34.627557+02	1	Res RES123 for Omarahmed	2	[{"changed": {"fields": ["Start time", "End time"]}}]	8	1
17	2026-03-19 15:01:15.130898+02	14	ABD-123 - 2026-03-19 12:07	2	[{"changed": {"fields": ["Car embedding"]}}]	9	1
18	2026-03-19 15:01:56.308755+02	15	ABG-123 - 2026-03-19 12:07	2	[{"changed": {"fields": ["Exit time", "Total fee", "Car embedding"]}}]	9	1
19	2026-03-19 15:03:55.13952+02	1	Camera CAM-01 - Zone zone-A1	2	[]	10	1
20	2026-03-19 15:16:39.250861+02	1	Camera CAM-01 - Zone zone-A1	2	[{"changed": {"fields": ["Col"]}}]	10	1
21	2026-03-19 15:16:54.457234+02	2	Camera CAM-02 - Zone zone-A16	1	[{"added": {}}]	10	1
22	2026-03-19 15:17:09.728565+02	3	Camera CAM-03 - Zone zone-A32	1	[{"added": {}}]	10	1
23	2026-03-19 15:23:28.363313+02	4	Camera CAM-04 - Zone zone-D1	1	[{"added": {}}]	10	1
24	2026-03-19 15:23:40.272461+02	5	Camera CAM-05 - Zone zone-D16	1	[{"added": {}}]	10	1
\.


--
-- TOC entry 5049 (class 0 OID 16390)
-- Dependencies: 220
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2026-03-04 13:10:27.916591+02
2	auth	0001_initial	2026-03-04 13:10:28.060286+02
3	admin	0001_initial	2026-03-04 13:10:28.106746+02
4	admin	0002_logentry_remove_auto_add	2026-03-04 13:10:28.1254+02
5	admin	0003_logentry_add_action_flag_choices	2026-03-04 13:10:28.146272+02
6	contenttypes	0002_remove_content_type_name	2026-03-04 13:10:28.183197+02
7	auth	0002_alter_permission_name_max_length	2026-03-04 13:10:28.20251+02
8	auth	0003_alter_user_email_max_length	2026-03-04 13:10:28.222731+02
9	auth	0004_alter_user_username_opts	2026-03-04 13:10:28.241153+02
10	auth	0005_alter_user_last_login_null	2026-03-04 13:10:28.261447+02
11	auth	0006_require_contenttypes_0002	2026-03-04 13:10:28.263547+02
12	auth	0007_alter_validators_add_error_messages	2026-03-04 13:10:28.29321+02
13	auth	0008_alter_user_username_max_length	2026-03-04 13:10:28.314635+02
14	auth	0009_alter_user_last_name_max_length	2026-03-04 13:10:28.334903+02
15	auth	0010_alter_group_name_max_length	2026-03-04 13:10:28.359901+02
16	auth	0011_update_proxy_permissions	2026-03-04 13:10:28.377885+02
17	auth	0012_alter_user_first_name_max_length	2026-03-04 13:10:28.398925+02
19	sessions	0001_initial	2026-03-04 13:10:28.552982+02
23	parking	0001_initial	2026-03-19 03:22:40.017658+02
24	parking	0002_reservation_license_plate	2026-03-19 04:02:58.009048+02
\.


--
-- TOC entry 5066 (class 0 OID 16632)
-- Dependencies: 237
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
vp08beyyc8au59ohiewusst17xvuyf2g	.eJxVjEEOwiAQRe_C2pAORQZcuu8ZyDCAVA0kpV0Z765NutDtf-_9l_C0rcVvPS1-juIiQJx-t0D8SHUH8U711iS3ui5zkLsiD9rl1GJ6Xg_376BQL9-awxlNdpiRtQoQR0SLFoCI0SoLZhiUcwQmJ3YaXFLJjnnMGjMppVG8P87dNy4:1w1m70:FQafauuE6hI221kTdQH9nLfah0NmK9DiG9Db-wLZM0k	2026-03-29 16:06:34.71341+02
\.


--
-- TOC entry 5068 (class 0 OID 24647)
-- Dependencies: 239
-- Data for Name: parking_camera; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_camera (id, camera_id, zone_name, "row", col) FROM stdin;
1	CAM-01	zone-A1	1	1
2	CAM-02	zone-A16	16	1
3	CAM-03	zone-A32	32	1
4	CAM-04	zone-D1	1	4
5	CAM-05	zone-D16	16	4
\.


--
-- TOC entry 5070 (class 0 OID 24662)
-- Dependencies: 241
-- Data for Name: parking_parkingslot; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_parkingslot (id, slot_number, status, slot_type, latitude, longitude, floor, "row", col) FROM stdin;
1	ENTER	active	entry	\N	\N	1	0	1
5	D2	available	car	\N	\N	1	2	5
6	B1	available	car	\N	\N	1	2	2
7	C1	available	car	\N	\N	1	2	3
8	A3	available	car	\N	\N	1	3	0
9	D3	available	car	\N	\N	1	3	5
10	B2	available	car	\N	\N	1	3	2
11	C2	available	car	\N	\N	1	3	3
12	A4	available	car	\N	\N	1	4	0
13	D4	available	car	\N	\N	1	4	5
14	B3	available	car	\N	\N	1	4	2
15	C3	available	car	\N	\N	1	4	3
16	A5	available	car	\N	\N	1	5	0
17	D5	available	car	\N	\N	1	5	5
18	B4	available	car	\N	\N	1	5	2
19	C4	available	car	\N	\N	1	5	3
20	A6	available	car	\N	\N	1	6	0
21	D6	available	car	\N	\N	1	6	5
22	B5	available	car	\N	\N	1	6	2
23	C5	available	car	\N	\N	1	6	3
24	A7	available	car	\N	\N	1	7	0
25	D7	available	car	\N	\N	1	7	5
26	B6	available	car	\N	\N	1	7	2
27	C6	available	car	\N	\N	1	7	3
28	A8	available	car	\N	\N	1	8	0
29	D8	available	car	\N	\N	1	8	5
30	B7	available	car	\N	\N	1	8	2
31	C7	available	car	\N	\N	1	8	3
32	A9	available	car	\N	\N	1	9	0
33	D9	available	car	\N	\N	1	9	5
34	B8	available	car	\N	\N	1	9	2
35	C8	available	car	\N	\N	1	9	3
36	A10	available	car	\N	\N	1	10	0
37	D10	available	car	\N	\N	1	10	5
38	B9	available	car	\N	\N	1	10	2
39	C9	available	car	\N	\N	1	10	3
40	A11	available	car	\N	\N	1	11	0
41	D11	available	car	\N	\N	1	11	5
42	B10	available	car	\N	\N	1	11	2
43	C10	available	car	\N	\N	1	11	3
44	A12	available	car	\N	\N	1	12	0
45	D12	available	car	\N	\N	1	12	5
46	B11	available	car	\N	\N	1	12	2
47	C11	available	car	\N	\N	1	12	3
48	A13	available	car	\N	\N	1	13	0
49	D13	available	car	\N	\N	1	13	5
50	B12	available	car	\N	\N	1	13	2
51	C12	available	car	\N	\N	1	13	3
52	A14	available	car	\N	\N	1	14	0
53	D14	available	car	\N	\N	1	14	5
54	B13	available	car	\N	\N	1	14	2
55	C13	available	car	\N	\N	1	14	3
56	A15	available	car	\N	\N	1	15	0
57	D15	available	car	\N	\N	1	15	5
58	B14	available	car	\N	\N	1	15	2
59	C14	available	car	\N	\N	1	15	3
60	A16	available	car	\N	\N	1	16	0
61	D16	available	car	\N	\N	1	16	5
62	B15	available	car	\N	\N	1	16	2
63	C15	available	car	\N	\N	1	16	3
64	A17	available	car	\N	\N	1	17	0
65	D17	available	car	\N	\N	1	17	5
66	B16	available	car	\N	\N	1	17	2
67	C16	available	car	\N	\N	1	17	3
68	A18	available	car	\N	\N	1	18	0
69	D18	available	car	\N	\N	1	18	5
70	A19	available	car	\N	\N	1	19	0
71	D19	available	car	\N	\N	1	19	5
72	A20	available	car	\N	\N	1	20	0
73	D20	available	car	\N	\N	1	20	5
74	A21	available	car	\N	\N	1	21	0
75	D21	available	car	\N	\N	1	21	5
76	A22	available	car	\N	\N	1	22	0
77	D22	available	car	\N	\N	1	22	5
78	A23	available	car	\N	\N	1	23	0
79	D23	available	car	\N	\N	1	23	5
80	A24	available	car	\N	\N	1	24	0
81	D24	available	car	\N	\N	1	24	5
82	A25	available	car	\N	\N	1	25	0
83	D25	available	car	\N	\N	1	25	5
84	A26	available	car	\N	\N	1	26	0
85	D26	available	car	\N	\N	1	26	5
86	A27	available	car	\N	\N	1	27	0
87	D27	available	car	\N	\N	1	27	5
88	A28	available	car	\N	\N	1	28	0
89	D28	available	car	\N	\N	1	28	5
90	A29	available	car	\N	\N	1	29	0
91	D29	available	car	\N	\N	1	29	5
92	A30	available	car	\N	\N	1	30	0
93	D30	available	car	\N	\N	1	30	5
94	A31	available	car	\N	\N	1	31	0
95	D31	available	car	\N	\N	1	31	5
96	A32	available	car	\N	\N	1	32	0
97	D32	available	car	\N	\N	1	32	5
98	A33	available	car	\N	\N	1	33	0
99	D33	available	car	\N	\N	1	33	5
100	A34	available	car	\N	\N	1	34	0
101	D34	available	car	\N	\N	1	34	5
102	A35	available	car	\N	\N	1	35	0
103	D35	available	car	\N	\N	1	35	5
104	A36	available	car	\N	\N	1	36	0
105	D36	available	car	\N	\N	1	36	5
106	A37	available	car	\N	\N	1	37	0
107	D37	available	car	\N	\N	1	37	5
3	D1	occupied	car	\N	\N	1	1	5
4	A2	occupied	car	\N	\N	1	2	0
108	A38	available	car	\N	\N	1	38	0
109	D38	available	car	\N	\N	1	38	5
110	A39	available	car	\N	\N	1	39	0
111	D39	available	car	\N	\N	1	39	5
112	A40	available	car	\N	\N	1	40	0
113	D40	available	car	\N	\N	1	40	5
114	A41	available	car	\N	\N	1	41	0
115	D41	available	car	\N	\N	1	41	5
116	A42	available	car	\N	\N	1	42	0
117	D42	available	car	\N	\N	1	42	5
118	A43	available	car	\N	\N	1	43	0
119	D43	available	car	\N	\N	1	43	5
120	A44	available	car	\N	\N	1	44	0
121	D44	available	car	\N	\N	1	44	5
122	A45	available	car	\N	\N	1	45	0
123	D45	available	car	\N	\N	1	45	5
124	A46	available	car	\N	\N	1	46	0
125	A47	available	car	\N	\N	1	47	0
126	A48	available	car	\N	\N	1	48	0
127	A49	available	car	\N	\N	1	49	0
128	A50	available	car	\N	\N	1	50	0
129	EXIT	active	exit	\N	\N	1	51	1
2	A1	occupied	car	\N	\N	1	1	0
\.


--
-- TOC entry 5072 (class 0 OID 24679)
-- Dependencies: 243
-- Data for Name: parking_reservation; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_reservation (id, reservation_code, start_time, end_time, created_at, is_active, slot_id, user_id, license_plate) FROM stdin;
1	RES123	2026-03-19 13:40:23+02	2026-03-19 14:40:25+02	2026-03-19 03:50:03.908499+02	t	2	4	ABC-123
\.


--
-- TOC entry 5074 (class 0 OID 24695)
-- Dependencies: 245
-- Data for Name: parking_vehiclelog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.parking_vehiclelog (id, license_plate, entry_image, exit_image, entry_time, exit_time, total_fee, is_paid, car_embedding, car_color, is_inside, last_seen, last_camera_id, slot_id) FROM stdin;
14	ABD-123	entry_pics/2026/03/19/car_lOfzd6V.jpg		2026-03-19 14:07:00.855431+02	\N	0.00	f	[0.1, 0.22, 0.23, 0.24, 0.54]	Black	t	2026-03-19 15:01:15.120164+02	1	3
15	ABG-123	entry_pics/2026/03/19/car_wgsVgUX.jpg		2026-03-19 14:07:15.872692+02	2026-03-19 15:01:31+02	-0.01	f	[0.1, 0.25, 0.53, 0.45, 0.55]	Black	t	2026-03-19 15:01:56.305911+02	1	4
13	ABC-123	entry_pics/2026/03/19/car_rO8kGWT.jpg		2026-03-19 13:59:50.544836+02	\N	0.00	f	[0.1, 0.2, 0.3, 0.4, 0.5]	Black	t	2026-03-19 13:59:50.545069+02	3	2
\.


--
-- TOC entry 5080 (class 0 OID 0)
-- Dependencies: 225
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- TOC entry 5081 (class 0 OID 0)
-- Dependencies: 227
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- TOC entry 5082 (class 0 OID 0)
-- Dependencies: 223
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 40, true);


--
-- TOC entry 5083 (class 0 OID 0)
-- Dependencies: 231
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- TOC entry 5084 (class 0 OID 0)
-- Dependencies: 229
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 4, true);


--
-- TOC entry 5085 (class 0 OID 0)
-- Dependencies: 233
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- TOC entry 5086 (class 0 OID 0)
-- Dependencies: 235
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 24, true);


--
-- TOC entry 5087 (class 0 OID 0)
-- Dependencies: 221
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 10, true);


--
-- TOC entry 5088 (class 0 OID 0)
-- Dependencies: 219
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 24, true);


--
-- TOC entry 5089 (class 0 OID 0)
-- Dependencies: 238
-- Name: parking_camera_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parking_camera_id_seq', 5, true);


--
-- TOC entry 5090 (class 0 OID 0)
-- Dependencies: 240
-- Name: parking_parkingslot_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parking_parkingslot_id_seq', 129, true);


--
-- TOC entry 5091 (class 0 OID 0)
-- Dependencies: 242
-- Name: parking_reservation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parking_reservation_id_seq', 1, true);


--
-- TOC entry 5092 (class 0 OID 0)
-- Dependencies: 244
-- Name: parking_vehiclelog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.parking_vehiclelog_id_seq', 15, true);


-- Completed on 2026-03-19 19:44:03

--
-- PostgreSQL database dump complete
--

\unrestrict L8QKrMpWwt4Hhu31s61EeszMI24LKLzYhAyyasimYr6ReRnPrfQUMQWtpYKoRwE

