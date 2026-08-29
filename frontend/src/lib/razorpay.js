import { api } from "@/lib/api";

/**
 * Open Razorpay Checkout modal for a booking.
 * Backend creates the order; frontend opens Razorpay; on success we verify.
 * Returns a Promise that resolves with the booking id on paid, rejects on cancel/error.
 */
export function payWithRazorpay(bookingId) {
  return new Promise(async (resolve, reject) => {
    if (typeof window.Razorpay === "undefined") {
      reject(new Error("Razorpay SDK not loaded"));
      return;
    }

    let orderPayload;
    try {
      const { data } = await api.post("/payments/checkout", {
        booking_id: bookingId,
        origin_url: window.location.origin,
      });
      orderPayload = data;
    } catch (err) {
      reject(err);
      return;
    }

    const options = {
      key: orderPayload.key_id,
      amount: orderPayload.amount, // paise
      currency: orderPayload.currency,
      name: "LABOS Technologies",
      description: orderPayload.project_title || "Service Booking",
      order_id: orderPayload.order_id,
      prefill: {
        name: orderPayload.customer_name || "",
        email: orderPayload.customer_email || "",
      },
      theme: { color: "#085DD4" },
      handler: async (response) => {
        try {
          await api.post("/payments/verify", {
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          resolve({ orderId: response.razorpay_order_id, bookingId: orderPayload.booking_id });
        } catch (err) {
          reject(err);
        }
      },
      modal: {
        ondismiss: () => reject(new Error("Payment cancelled")),
      },
    };

    const rz = new window.Razorpay(options);
    rz.on("payment.failed", (resp) => {
      reject(new Error(resp?.error?.description || "Payment failed"));
    });
    rz.open();
  });
}
