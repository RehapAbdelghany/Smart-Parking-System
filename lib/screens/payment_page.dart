import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/payment_provider.dart';
import 'navigation_page.dart';

class PaymentPage extends StatefulWidget {
  final int hours;
  final String slotId; // ✅ أضفنا slotId

  const PaymentPage({
    super.key,
    required this.hours,
    required this.slotId,
  });

  @override
  State<PaymentPage> createState() => _PaymentPageState();
}

class _PaymentPageState extends State<PaymentPage> {
  final TextEditingController visaNumberController = TextEditingController();
  final TextEditingController visaHolderController = TextEditingController();
  final TextEditingController visaExpiryController = TextEditingController();
  final TextEditingController visaCvvController = TextEditingController();

  final TextEditingController masterNumberController = TextEditingController();
  final TextEditingController masterHolderController = TextEditingController();
  final TextEditingController masterExpiryController = TextEditingController();
  final TextEditingController masterCvvController = TextEditingController();

  String selectedMethod = "";

  List<PaymentMethodModel> methods = [
    PaymentMethodModel(title: "Apple Pay", icon: Icons.apple),
    PaymentMethodModel(title: "Visa", icon: Icons.credit_card),
    PaymentMethodModel(title: "Mastercard", icon: Icons.payment),
  ];

  @override
  Widget build(BuildContext context) {
    final provider = Provider.of<PaymentProvider>(context);

    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: const Text(
          "Payment",
          style: TextStyle(color: Color(0xFF333333)),
        ),
        centerTitle: true,
        backgroundColor: const Color(0xFF09D0B3),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            children: [
              // Parking details
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFFF2F2F2),
                  borderRadius: BorderRadius.circular(15),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "Parking Session Details",
                      style: TextStyle(
                          color: Color(0xFF333333),
                          fontSize: 18,
                          fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Hours",
                            style: TextStyle(
                                fontSize: 16, color: Color(0xFF333333))),
                        Text(
                          widget.hours.toString(),
                          style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF333333)),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text("Price per hour",
                            style: TextStyle(
                                fontSize: 16, color: Color(0xFF333333))),
                        Text(
                          "${provider.pricePerHour.toStringAsFixed(2)} EGP",
                          style: const TextStyle(
                              fontSize: 16, color: Color(0xFF333333)),
                        ),
                      ],
                    ),
                    const Divider(height: 30),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          "Total Price",
                          style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF333333)),
                        ),
                        Text(
                          "${provider.totalPriceForHours(widget.hours).toStringAsFixed(2)} EGP",
                          style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF00A896)),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 30),
              const Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  "Payment Methods",
                  style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF333333)),
                ),
              ),
              const SizedBox(height: 15),
              StatefulBuilder(builder: (context, setState) {
                return Column(
                  children: methods
                      .map((method) => _paymentButton(method, setState))
                      .toList(),
                );
              }),
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton(
                  onPressed: () {
                    Map<String, dynamic> paymentData = {};

                    if (selectedMethod == "Visa") {
                      paymentData = {
                        "method": "Visa",
                        "number": visaNumberController.text,
                        "holder": visaHolderController.text,
                        "expiry": visaExpiryController.text,
                        "cvv": visaCvvController.text,
                        "hours": widget.hours,
                        "totalPrice":
                        provider.totalPriceForHours(widget.hours),
                      };
                    } else if (selectedMethod == "Mastercard") {
                      paymentData = {
                        "method": "Mastercard",
                        "number": masterNumberController.text,
                        "holder": masterHolderController.text,
                        "expiry": masterExpiryController.text,
                        "cvv": masterCvvController.text,
                        "hours": widget.hours,
                        "totalPrice":
                        provider.totalPriceForHours(widget.hours),
                      };
                    }

                    Provider.of<PaymentProvider>(context, listen: false)
                        .processPayment(paymentData);

                    // ✅ بعد الدفع روح على NavigationPage
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => NavigationPage(slotId: widget.slotId),
                      ),
                    );
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00A896),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(15)),
                  ),
                  child: const Text(
                    "Confirm Payment",
                    style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold),
                  ),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _paymentButton(
      PaymentMethodModel method, void Function(void Function()) setState) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: const Color(0xFFF2F2F2),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          ListTile(
            leading: Icon(method.icon, color: const Color(0xFF00A896)),
            title: Text(method.title,
                style: const TextStyle(color: Color(0xFF333333))),
            trailing: Icon(
                method.isExpanded
                    ? Icons.keyboard_arrow_down
                    : Icons.arrow_forward_ios,
                color: const Color(0xFF00A896)),
            onTap: () {
              setState(() {
                method.isExpanded = !method.isExpanded;
                selectedMethod = method.title;
              });
            },
          ),
          if (method.isExpanded) _buildPaymentInputs(method.title),
        ],
      ),
    );
  }

  Widget _buildPaymentInputs(String method) {
    switch (method) {
      case "Visa":
        return Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              _inputField("Card Number", visaNumberController),
              _inputField("Card Holder Name", visaHolderController),
              Row(
                children: [
                  Expanded(
                      child: _inputField(
                          "Expiry MM/YY", visaExpiryController)),
                  const SizedBox(width: 10),
                  Expanded(
                      child: _inputField("CVV", visaCvvController)),
                ],
              ),
            ],
          ),
        );
      case "Mastercard":
        return Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              _inputField("Card Number", masterNumberController),
              _inputField("Card Holder Name", masterHolderController),
              Row(
                children: [
                  Expanded(
                      child: _inputField(
                          "Expiry MM/YY", masterExpiryController)),
                  const SizedBox(width: 10),
                  Expanded(
                      child: _inputField("CVV", masterCvvController)),
                ],
              ),
            ],
          ),
        );
      default:
        return Container();
    }
  }

  Widget _inputField(String label, TextEditingController controller) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          labelStyle: const TextStyle(color: Color(0xFF333333)),
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFF00A896)),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFF00A896)),
          ),
        ),
      ),
    );
  }
}

class PaymentMethodModel {
  final String title;
  final IconData icon;
  bool isExpanded;

  PaymentMethodModel(
      {required this.title, required this.icon, this.isExpanded = false});
}