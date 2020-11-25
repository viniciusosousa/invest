#include <stdio.h>
#include <stdlib.h>
#include "sqlite3.h"

char* file_get_contents(char*);
sqlite3* initDB();

int main(int argc, char *argv[]){
	sqlite3 *db = NULL;
	db = initDB();
	if(!db){
	    printf("Erro ao abrir o banco");
	    exit(1);
	}
       return 0;
}

sqlite3* initDB(){
    const char dbname[]="invest.db";
    sqlite3 *db = NULL;
    FILE *fp = NULL;
    char *err = NULL;
    int rc= 0, flInit = 0;

    /* Verifica se o banco de dado ja existe. 
    Senao define que ele deve ser inicializado 
    */
    fp = fopen(dbname, "rb");
    if (!fp) {flInit =1;}
    else {fclose(fp);}
    rc = sqlite3_open(dbname, &db);

    if (rc!=SQLITE_OK){
	fprintf(stderr, "Não foi possivel abrir o banco: %s\n", sqlite3_errmsg(db));
	sqlite3_close(db);
	return NULL;
    }

    if(flInit){
	char *SQL=NULL;
	SQL = file_get_contents("install/initdb.sql");	
	rc = sqlite3_exec(db, SQL, NULL, NULL, &err);
	if ( rc != SQLITE_OK ) {
	    fprintf (stderr, "Erro ao executar o SQL: %s\n", err);
	    sqlite3_free(err);
	}
    }
    return db;

}

char* file_get_contents(char *filename){
	long len;
	FILE *fp;
	char *buffer = NULL;

	if((fp = fopen(filename,"r"))==NULL){
	    printf("Erro ao abrir arquivo");
	    exit(1);
	 }
	fseek(fp, 0, SEEK_END);
	len = ftell(fp);
	fseek(fp, 0, SEEK_SET);
	buffer = malloc(len+1);
	if (buffer){
	    fread(buffer, 1, len, fp);
	    buffer[len]='\0';
	}
	fclose(fp);
	return buffer;	
}
