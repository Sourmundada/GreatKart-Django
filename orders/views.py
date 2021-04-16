from django.shortcuts import render, redirect
from cart.models import Cart, CartItem
from .forms import OrderForm
from .models import Payment, Order, OrderProduct
from django.contrib.auth.decorators import login_required
from store.models import Product
from django.http import JsonResponse
import datetime
import json
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move cart_item to orderProduct.

    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        order_product = OrderProduct()
        order_product.order_id = order.id
        order_product.payment = payment
        order_product.user_id = request.user.id
        order_product.product_id = item.product_id
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=order_product.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()

    # Reduce the quantity of sold products.

        product = Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        product.save()


    # clear the user cart.

    CartItem.objects.filter(user=request.user).delete()

    # send order recieved mail.
    mail_subject = 'Thank You For Buying Our Product!'
    message = render_to_string('app/order_recieved_email.html', {
        'user': request.user,
        'order': order,
        })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    
    # send_order number & transaction id to sendData() via json
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }

    return JsonResponse(data)

    return render(request, 'app/payments.html')


@login_required(login_url='login')
def place_order(request, total=0, quantity=0):
    current_user = request.user

    # Cart count <= 0, redirect to store.
    cart_items = CartItem.objects.filter(user=current_user)

    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    
    tax = (2 * total)/100
    grand_total = total + tax
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # store billing details
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.pin_code = form.cleaned_data['pin_code']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date = d.strftime("%Y%m%d") #20210305
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order' : order,
                'cart_items': cart_items,
                'tax': tax,
                'total': total,
                'grand_total': grand_total,
            }

            return render(request, 'app/payments.html', context=context)
        else:
            return redirect('checkout')

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        payment = Payment.objects.get(payment_id=transID)

        sub_total = 0
        for i in ordered_products:
            sub_total += i.product_price * i.quantity

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'sub_total': sub_total,
            
        } 
        return render(request, 'app/order_completed.html', context=context)

    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')