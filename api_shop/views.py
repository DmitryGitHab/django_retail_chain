from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import URLValidator
from requests import get
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader

from .serializers import UserSerializer, ContactSerializer, ShopSerializer, CategorySerializer,\
    ProductSerializer, OrderItemSerializer, OrderSerializer, OrderModifySerializer, OrderItemAddSerializer
from .models import ConfirmEmailToken, Contact, Shop, Category, Product, Parameter, ProductParameter, Order, OrderItem


class RegisterAccount(APIView):
    """
    Для регистрации покупателей
    """
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                return Response({'status': False, 'error': {'password': password_error}},
                                status=status.HTTP_403_FORBIDDEN)
            else:
                # проверяем данные для уникальности имени пользователя
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    user = user_serializer.save()
                    user.set_password(request.data['password'])
                    user.save()
                    token, _ = ConfirmEmailToken.objects.get_or_create(user_id=user.id)
                    user.email_user(f'Token для подтверждения регистрации пользователя {token.user.email}',
                                    token.key,
                                    from_email=settings.EMAIL_HOST_USER)
                    # new_user_registered.send(sender=self.__class__, user_id=user.id)
                    return Response({'status': True})
                else:
                    return Response({'status': False, 'error': user_serializer.errors},
                                    status=status.HTTP_403_FORBIDDEN)
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class ConfirmAccount(APIView):
    """
    Класс для подтверждения почтового адреса
    """
    def post(self, request, *args, **kwargs):
        # проверяем обязательные аргументы
        if {'email', 'token'}.issubset(request.data):

            token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                     key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'status': True})
            else:
                return Response({'status': False, 'error': 'Неправильно указан токен или email'},
                                status=status.HTTP_403_FORBIDDEN)
        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class LoginAccount(APIView):
    """
    Класс для авторизации пользователей
    """
    def post(self, request, *args, **kwargs):
        if {'email', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['email'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)

                    return Response({'status': True, 'token': token.key})

            return Response({'status': False, 'error': 'Не удалось авторизовать'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)


class AccountDetails(APIView):
    """
    Класс для работы данными пользователя
    """
    # Возвращает все данные пользователя включая все контакты.
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    # Изменяем данные пользователя.
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Login required'}, status=status.HTTP_403_FORBIDDEN)

        # Если есть пароль, проверяем его и сохраняем.
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                return Response({'status': False, 'error': {'password': password_error}},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                request.user.set_password(request.data['password'])

        # Проверяем остальные данные
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'status': True}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': False, 'error': user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ContactView(APIView):
    """
    Класс для работы с контактами пользователей
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        contact = Contact.objects.filter(user__id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # Добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)



        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            print(request.user.id)
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return Response({'status': True}, status=status.HTTP_201_CREATED)
            else:
                Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Редактируем контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if {'id'}.issubset(request.data):
            try:
                contact = Contact.objects.get(pk=int(request.data["id"]))
            except ValueError:
                return Response(
                    {'status': False, 'error': 'Неверный тип аргумента ID.'}, status=status.HTTP_400_BAD_REQUEST)
            except ObjectDoesNotExist:
                return Response(
                    {'status': False, 'error': f"Контакта с ID={request.data['id']} не существует."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ContactSerializer(contact, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'status': True}, status=status.HTTP_200_OK)
            return Response({'status': False, 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Удаляем указанные контакты
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Вы не авторизовались!'}, status=status.HTTP_403_FORBIDDEN)

        if {'items'}.issubset(request.data):
            for item in request.data["items"].split(','):
                try:
                    contact = Contact.objects.get(pk=int(item))
                    contact.delete()
                except ValueError:
                    return Response({'status': False, 'error': 'Неверный тип аргумента (items).'},
                                    status=status.HTTP_400_BAD_REQUEST)
                except ObjectDoesNotExist:
                    return Response({'status': False, 'error': f'Контакта с ID={item} не существует.'},
                                    status=status.HTTP_400_BAD_REQUEST)
            return Response({'status': True}, status=status.HTTP_204_NO_CONTENT)

        return Response({'status': False, 'error': 'Не указаны ID контактов'},
                        status=status.HTTP_400_BAD_REQUEST)


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def _import_product(self, product_data, shop_id):
        product = Product(name=product_data['name'],
                          category_id=product_data['category'],
                          model=product_data['model'],
                          external_id=product_data['id'],
                          shop_id=shop_id,
                          quantity=product_data['quantity'],
                          price=product_data['price'],
                          price_rrc=product_data['price_rrc'])
        return product

    def _import_parameter(self, parameter_list, items_dict, prod):
        for key, value in items_dict[prod.external_id].items():
            parameter_list.append(ProductParameter(product_id=prod.id,
                                                   parameter_id=key,
                                                   value=value))

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'status': False, 'error': 'Log in required'}, status=status.HTTP_403_FORBIDDEN)

        if request.user.type != 'shop':
            return Response({'status': False, 'error': 'Только для магазинов'}, status=status.HTTP_403_FORBIDDEN)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return Response({'status': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                stream = get(url).content

                data = load_yaml(stream, Loader=Loader)

                shop, _ = Shop.objects.get_or_create(user_id=request.user.id,
                                                     defaults={'name': data['shop'], 'url': url})
                if shop.name != data['shop']:
                    return Response({'status': False, 'error': 'В прайсе указано некорректное название магазина!'},
                                    status=status.HTTP_400_BAD_REQUEST)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()
                Product.objects.filter(shop_id=shop.id).delete()
                product_items = []
                parameter_items = {}
                parameter_list = []
                for item in data['goods']:
                    product_items.append(self._import_product(item, shop.id))
                    parameter_items[item['id']] = {}
                    for name, value in item['parameters'].items():
                        parameter, _ = Parameter.objects.get_or_create(name=name)
                        parameter_items[item['id']].update({parameter.id: value})

                list_of_products = Product.objects.bulk_create(product_items)

                for product in list_of_products:
                    self._import_parameter(parameter_list, parameter_items, product)

                ProductParameter.objects.bulk_create(parameter_list)

                return Response({'status': True})

        return Response({'status': False, 'error': 'Не указаны все необходимые аргументы'},
                        status=status.HTTP_400_BAD_REQUEST)
