$(function (){
    var IMP = window.IMP; //iamport 매뉴얼 참고
    IMP.init('imp55982320'); //가맹점 식별코드

    $('.order-form').on('submit',function (e){
        var amount = parseFloat($('.order-form input[name="amount"]').val().replace(',','')); //결제 금액
        var type = $('.order-form input[name="type"]:checked').val(); // 결제 타입 결정

        console.log("line9", amount);
        // 폼 데이터를 기준으로 주문 생성
        var order_id = AjaxCreateOrder(e); //결제하기 누르면 주문이 생성

        if(order_id == false){
            alert('주문 생성 실패 \n 다시 시도해주세요.')
            return false; // form 이 동작하지 않음
        }

        // 결제 정보 생성
        var merchant_id = AjaxStoreTransaction(e, order_id, amount, type);

        // 결제 정보가 만들어졌으면, iamport로 실제 결제 시도
        if(merchant_id !== ''){
            console.log("line23.어디에..");
            IMP.request_pay({
                merchant_uid : merchant_id,
                name : 'E-Shop product', // 임의의 이름
                buyer_name:$('input[name="first_name"]').val()+" "+$('input[name="last_name"]').val(),
                buyer_email:$('input[name="email"]').val(),
                amount:amount
            }, function(rsp){
                if (rsp.success){
                    console.log(".js line 31 : 넘어오는 거 맞니");
                    var msg = '결제가 완료되었습니다.';
                    msg += '고유 ID : ' + rsp.imp_uid;
                    msg += '상점 거래ID : '+ rsp.merchant_uid;
                    console.log("line35"+rsp.paid_amount);
                    msg += '결제 금액 : ' + rsp.paid_amount;
                    msg += '카드 승인번호 : ' + rsp.apply_num;
                    // 결제가 완료되었으면, 비교해서 DB 반영
                    ImpTransaction(e, order_id, rsp.merchant_uid, rsp.imp_uid, rsp.paid_amount);
                } else {
                    var msg = '결제에 실패하였습니다. ';
                    msg += '에러내용 : ' + rsp.error_msg;
                    console.log(msg);
                }
            });
        }
        return false;
    });
});

function AjaxCreateOrder(e){
    e.preventDefault(); //form이 sumit 되는 거 방지
    var order_id = '';

    var request = $.ajax({
        method:"POST",
        url: order_create_url, //order 생성 뷰 호출, templates에 준비해둔 url임
        async: false,
        data:$('.order-form').serialize() //serailize()를 통해 form의 객체들을 한번에 가져옴
    });

    // 응답 오면 처리하는 부분
    request.done(function (data){
        if (data.order_id){
            order_id = data.order_id;
        }
    });

    // 응답이 왔는데 문제가 있을 때 처리
    request.fail(function(jqXHR, textStatus){
        if (jqXHR.status==404){
            alert("페이지가 존재하지 않습니다.");
        } else if (jqXHR.status ==403){
            alert("로그인 해주세요.");
        } else {
            alert("문제가 발생했습니다. 다시 시도해주세요.");
        }
    });
    return order_id;
}

function AjaxStoreTransaction(e, order_id, amount, type){
    e.preventDefault();
    var merchant_id = '';
    var request = $.ajax({
        method: "POST",
        url : order_checkout_url, //OrderCheckoutAjaxView 호출
        async:false,
        data: {
            order_id : order_id,
            amount : amount,
            type : type,
            csrfmiddlewaretoken: csrf_token, //create.html 에 정의됨
        }
    });

    request.done(function(data) {
        if (data.works){
            merchant_id = data.merchant_id;
        }
    });

    request.fail(function (jqXHR, textStatus){
        if (jqXHR.status==404){
            alert("페이지가 존재하지 않습니다.");
        } else if (jqXHR.status == 403){
            alert("로그인 해주세요.");
        } else {
            alert("문제가 발생했습니다. 다시 시도해주세요.");
        }
    });
    return merchant_id;
}

function ImpTransaction(e, order_id, merchant_id, imp_id, amount){
    e.preventDefault();
    var request = $.ajax({
        method:"POST",
        url:order_validation_url,
        async: false,
        data: {
            order_id : order_id,
            merchant_id : merchant_id,
            imp_id : imp_id,
            amount : amount,
            csrfmiddlewaretoken : csrf_token
        }
    });

    request.done(function (data){
    console.log("line131. 완료..?")
        if (data.works) {
            $(location).attr('href', location.origin + order_complete_url + '?order_id=' + order_id)
        }
    });

    request.fail(function(jqXHR, textStatus){
        if (jqXHR.status==404){
            alert("페이지가 존재하지 않습니다.");
        } else if (jqXHR.status == 403){
            alert("로그인 해주세요.");
        } else {
            alert("문제가 발생했습니다. 다시 시도해주세요. ");
        }
    });
}